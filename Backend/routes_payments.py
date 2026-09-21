from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import (
    User, TariffPlan, UserSubscription, Payment,
)
from schemas import (
    TariffPlanSchema, UserSubscriptionSchema, PaymentSchema, CreatePaymentSchema,
)
from auth import get_current_user
from payment_service import payment_service, EXPRESS_PAY_BASE_URL

payments_router = APIRouter(prefix="/payments", tags=["Payments"])


# ──────────────────────────── Create Payment ────────────────────────────


@payments_router.post("/create/")
async def create_payment(
    data: CreatePaymentSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TariffPlan).where(TariffPlan.id == data.plan_id, TariffPlan.is_active == True)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Tariff plan not found")

    result = await db.execute(
        select(UserSubscription).where(
            UserSubscription.user_id == user.id,
            UserSubscription.status == "active",
        )
    )
    active_sub = result.scalar_one_or_none()
    if active_sub:
        raise HTTPException(status_code=400, detail="You already have an active subscription")

    sub = UserSubscription(
        user_id=user.id,
        plan_id=plan.id,
        status="pending",
    )
    db.add(sub)
    await db.flush()

    from datetime import timedelta
    invoice_no = payment_service.generate_invoice_number()
    payment = Payment(
        user_id=user.id,
        subscription_id=sub.id,
        invoice_no=invoice_no,
        amount=plan.price,
        status="pending",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    if plan.price == 0:
        from datetime import timedelta
        sub.status = "active"
        sub.started_at = datetime.now(timezone.utc)
        sub.expires_at = datetime.now(timezone.utc) + timedelta(days=plan.duration_days)
        payment.status = "completed"
        payment.paid_at = datetime.now(timezone.utc)
        user.current_plan = plan.name
        await db.commit()
        return {
            "detail": "Free plan activated",
            "payment_id": payment.id,
            "invoice_no": invoice_no,
            "status": "completed",
        }

    invoice_result = await payment_service.create_invoice(
        amount=plan.price,
        invoice_no=invoice_no,
        description=f"CareerHub {plan.display_name} - {plan.duration_days} days",
        email=user.email,
        extra_data={"user_id": user.id, "subscription_id": sub.id, "plan_id": plan.id},
    )

    if not invoice_result.get("success"):
        payment.status = "failed"
        sub.status = "cancelled"
        await db.commit()
        raise HTTPException(status_code=502, detail=f"Payment gateway error: {invoice_result.get('error')}")

    return {
        "payment_id": payment.id,
        "invoice_no": invoice_no,
        "invoice_url": invoice_result.get("invoice_url", ""),
        "amount": plan.price,
        "plan": TariffPlanSchema.model_validate(plan),
    }


# ──────────────────────────── Payment Webhook ────────────────────────────


@payments_router.post("/webhook/")
async def payment_webhook(data: dict, db: AsyncSession = Depends(get_db)):
    from payment_service import DushanbeCityPayment

    if not DushanbeCityPayment.verify_webhook_signature(data):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = DushanbeCityPayment.parse_webhook_payload(data)
    invoice_no = payload.get("invoice_no", "")
    new_status = payload.get("status", "")

    result = await db.execute(
        select(Payment).where(Payment.invoice_no == invoice_no)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if new_status in ("completed", "paid", "success"):
        payment.status = "completed"
        payment.paid_at = datetime.now(timezone.utc)
        payment.payment_method = payload.get("payment_method", "")

        sub_result = await db.execute(
            select(UserSubscription).where(UserSubscription.id == payment.subscription_id)
        )
        subscription = sub_result.scalar_one_or_none()
        if subscription:
            from datetime import timedelta
            now = datetime.now(timezone.utc)
            subscription.status = "active"
            subscription.started_at = now
            subscription.expires_at = now + timedelta(days=subscription.plan.duration_days if subscription.plan else 30)

            plan_result = await db.execute(
                select(TariffPlan).where(TariffPlan.id == subscription.plan_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                user_result = await db.execute(
                    select(User).where(User.id == payment.user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    user.current_plan = plan.name

    elif new_status in ("cancelled", "failed", "expired"):
        payment.status = new_status
        sub_result = await db.execute(
            select(UserSubscription).where(UserSubscription.id == payment.subscription_id)
        )
        subscription = sub_result.scalar_one_or_none()
        if subscription:
            subscription.status = "cancelled"

    await db.commit()

    return {"status": "ok"}


# ──────────────────────────── My Subscription ────────────────────────────


@payments_router.get("/my-subscription/")
async def get_my_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserSubscription)
        .where(
            UserSubscription.user_id == user.id,
            UserSubscription.status == "active",
        )
        .order_by(UserSubscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        return {
            "has_subscription": False,
            "plan": None,
            "subscription": None,
        }

    plan_result = await db.execute(
        select(TariffPlan).where(TariffPlan.id == subscription.plan_id)
    )
    plan = plan_result.scalar_one_or_none()

    return {
        "has_subscription": True,
        "plan": TariffPlanSchema.model_validate(plan) if plan else None,
        "subscription": {
            "id": subscription.id,
            "status": subscription.status,
            "started_at": subscription.started_at.isoformat() if subscription.started_at else None,
            "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
            "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
        },
    }


# ──────────────────────────── Payment History ────────────────────────────


@payments_router.get("/history/")
async def payment_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc())
    )
    payments = result.scalars().all()

    history = []
    for p in payments:
        plan_info = None
        sub_result = await db.execute(
            select(UserSubscription).where(UserSubscription.id == p.subscription_id)
        )
        sub = sub_result.scalar_one_or_none()
        if sub:
            plan_result = await db.execute(
                select(TariffPlan).where(TariffPlan.id == sub.plan_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                plan_info = TariffPlanSchema.model_validate(plan)

        history.append({
            "id": p.id,
            "invoice_no": p.invoice_no,
            "amount": p.amount,
            "status": p.status,
            "payment_method": p.payment_method,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "subscription_plan": plan_info,
        })

    return history


# ──────────────────────────── Check Access ────────────────────────────


PLAN_FEATURES = {
    "free": {
        "max_resumes": 1,
        "max_applications_per_day": 5,
        "can_download_pdf": False,
        "can_message_employers": False,
        "can_see_analytics": False,
        "can_highlight_resume": False,
        "priority_support": False,
    },
    "basic": {
        "max_resumes": 3,
        "max_applications_per_day": 20,
        "can_download_pdf": True,
        "can_message_employers": True,
        "can_see_analytics": False,
        "can_highlight_resume": False,
        "priority_support": False,
    },
    "pro": {
        "max_resumes": 10,
        "max_applications_per_day": 100,
        "can_download_pdf": True,
        "can_message_employers": True,
        "can_see_analytics": True,
        "can_highlight_resume": True,
        "priority_support": True,
    },
    "enterprise": {
        "max_resumes": -1,
        "max_applications_per_day": -1,
        "can_download_pdf": True,
        "can_message_employers": True,
        "can_see_analytics": True,
        "can_highlight_resume": True,
        "priority_support": True,
    },
}


@payments_router.get("/check-access/")
async def check_access(
    feature: str = Query(..., description="Feature name to check"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan_name = user.current_plan or "free"

    if plan_name not in PLAN_FEATURES:
        plan_name = "free"

    features = PLAN_FEATURES.get(plan_name, PLAN_FEATURES["free"])

    if feature not in features:
        return {
            "feature": feature,
            "has_access": False,
            "current_plan": plan_name,
            "message": f"Unknown feature: {feature}",
        }

    value = features[feature]
    has_access = bool(value) if not isinstance(value, int) else (value != 0)

    result = await None
    if user.current_plan and user.current_plan != "free":
        sub_result = await db.execute(
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user.id,
                UserSubscription.status == "active",
            )
        )
        sub = sub_result.scalar_one_or_none()
        if sub and sub.expires_at:
            from datetime import datetime, timezone as tz
            if sub.expires_at.replace(tzinfo=tz.utc) < datetime.now(tz.utc):
                has_access = False

    return {
        "feature": feature,
        "has_access": has_access,
        "value": value,
        "current_plan": plan_name,
    }
