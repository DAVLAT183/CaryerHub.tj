from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timezone
import re as _re
from database import get_db
from models import (
    User,
    StudentProfile,
    EmployerProfile,
    Category,
    WorkSchedule,
    WorkFormat,
    WorkExperience,
    DirectMessage,
    Job,
)
from schemas import (
    UserResponse,
    UserUpdateRequest,
    ChangePasswordRequest,
    StudentProfileResponse,
    StudentProfileCreate,
    EmployerProfileResponse,
    EmployerProfileCreate,
    CategoryResponse,
    CategoryCreate,
)
from auth import get_current_user, get_optional_user, hash_password, verify_password


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = _re.sub(r'[^\w\s-]', '', text)
    text = _re.sub(r'[\s_]+', '-', text)
    return text.strip('-')

router = APIRouter(tags=["Profiles"])


@router.get("/users/", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.is_staff:
        result = await db.execute(select(User))
        return result.scalars().all()

    partner_ids = set()
    dms = await db.execute(
        select(DirectMessage).where(
            (DirectMessage.sender_id == current_user.id)
            | (DirectMessage.recipient_id == current_user.id)
        )
    )
    for dm in dms.scalars().all():
        if dm.sender_id != current_user.id:
            partner_ids.add(dm.sender_id)
        if dm.recipient_id != current_user.id:
            partner_ids.add(dm.recipient_id)

    if not partner_ids:
        return []

    result = await db.execute(select(User).where(User.id.in_(partner_ids)))
    return result.scalars().all()


@router.get("/users/me/", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.patch("/users/me/", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/users/me/change-password/")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=400,
            detail="Password login is not available for this account (signed in via Google)",
        )

    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=400, detail="New password must differ from the current one")

    current_user.hashed_password = hash_password(payload.new_password)
    await db.commit()
    return {"detail": "Password updated successfully"}


@router.get("/users/me/export/")
async def export_my_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from models import Resume, Application, Favorite, Notification, Payment

    student_profile = (await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )).scalar_one_or_none()
    employer_profile = (await db.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == current_user.id)
    )).scalar_one_or_none()

    resumes_data = []
    applications_data = []
    favorites_data = []
    jobs_data = []

    if student_profile:
        resumes = (await db.execute(
            select(Resume).where(Resume.student_id == student_profile.id)
        )).scalars().all()
        resumes_data = [
            {
                "id": r.id,
                "title": r.title,
                "about": r.about,
                "skills": r.skills,
                "schedule_type": r.schedule_type,
                "work_format": r.work_format,
                "github_url": r.github_url,
                "portfolio_url": r.portfolio_url,
                "linkedin_url": r.linkedin_url,
                "style": r.style,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in resumes
        ]

        apps = (await db.execute(
            select(Application).where(
                Application.resume_id.in_(
                    select(Resume.id).where(Resume.student_id == student_profile.id)
                )
            )
        )).scalars().all()
        applications_data = [
            {
                "id": a.id,
                "job_id": a.job_id,
                "resume_id": a.resume_id,
                "status": a.status,
                "cover_letter": a.cover_letter,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in apps
        ]

        favs = (await db.execute(
            select(Favorite).where(Favorite.student_id == student_profile.id)
        )).scalars().all()
        favorites_data = [
            {"job_id": f.job_id, "created_at": f.created_at.isoformat() if f.created_at else None}
            for f in favs
        ]

    if employer_profile:
        jobs = (await db.execute(
            select(Job).where(Job.employer_id == employer_profile.id)
        )).scalars().all()
        jobs_data = [
            {
                "id": j.id,
                "title": j.title,
                "description": j.description,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "schedule": j.schedule,
                "work_format": j.work_format,
                "is_active": j.is_active,
                "views_count": j.views_count or 0,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ]

    notifications = (await db.execute(
        select(Notification).where(Notification.user_id == current_user.id)
    )).scalars().all()
    notifications_data = [
        {
            "id": n.id,
            "type": n.notification_type,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]

    payments = (await db.execute(
        select(Payment).where(Payment.user_id == current_user.id)
    )).scalars().all()
    payments_data = [
        {
            "invoice_no": p.invoice_no,
            "amount": p.amount,
            "status": p.status,
            "payment_method": p.payment_method,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in payments
    ]

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "profile": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "role": current_user.role,
            "phone": current_user.phone,
            "location": current_user.location,
            "avatar": current_user.avatar,
            "is_email_verified": current_user.is_email_verified,
            "current_plan": current_user.current_plan,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "student_profile": {
            "university": student_profile.university,
            "faculty": student_profile.faculty,
            "course": student_profile.course,
            "birth_date": student_profile.birth_date,
            "age": student_profile.age,
            "city": student_profile.city,
            "views_count": student_profile.views_count or 0,
        } if student_profile else None,
        "employer_profile": {
            "company_name": employer_profile.company_name,
            "description": employer_profile.description,
            "website": employer_profile.website,
            "address": employer_profile.address,
            "is_verified": employer_profile.is_verified,
            "views_count": employer_profile.views_count or 0,
        } if employer_profile else None,
        "resumes": resumes_data,
        "applications": applications_data,
        "favorites": favorites_data,
        "jobs": jobs_data,
        "notifications": notifications_data,
        "payments": payments_data,
    }


@router.get("/student-profiles/", response_model=List[StudentProfileResponse])
async def list_student_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudentProfile))
    return result.scalars().all()


@router.get("/student-profiles/{profile_id}", response_model=StudentProfileResponse)
async def get_student_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


@router.post(
    "/student-profiles/",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_student_profile(
    profile_data: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Student profile already exists for this user"
        )
    profile = StudentProfile(user_id=current_user.id, **profile_data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/student-profiles/{profile_id}/view/")
async def track_student_profile_view(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = (await db.execute(
        select(StudentProfile).where(StudentProfile.id == profile_id)
    )).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    if profile.user_id != current_user.id:
        profile.views_count = (profile.views_count or 0) + 1
        await db.commit()
        await db.refresh(profile)

    return {"views_count": profile.views_count}


@router.post("/employer-profiles/{profile_id}/view/")
async def track_employer_profile_view(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = (await db.execute(
        select(EmployerProfile).where(EmployerProfile.id == profile_id)
    )).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Employer profile not found")

    if profile.user_id != current_user.id:
        profile.views_count = (profile.views_count or 0) + 1
        await db.commit()
        await db.refresh(profile)

    return {"views_count": profile.views_count}


@router.api_route(
    "/student-profiles/{profile_id}",
    methods=["PUT", "PATCH"],
    response_model=StudentProfileResponse,
)
async def update_student_profile(
    profile_id: int,
    profile_data: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    if profile.user_id != current_user.id and not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.delete("/student-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    if profile.user_id != current_user.id and not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to delete this profile")
    await db.delete(profile)
    await db.commit()


@router.get("/employer-profiles/", response_model=List[EmployerProfileResponse])
async def list_employer_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EmployerProfile))
    return result.scalars().all()


@router.get("/employer-profiles/{profile_id}", response_model=EmployerProfileResponse)
async def get_employer_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    return profile


@router.post(
    "/employer-profiles/",
    response_model=EmployerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_employer_profile(
    profile_data: EmployerProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Employer profile already exists for this user"
        )
    profile = EmployerProfile(user_id=current_user.id, **profile_data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.api_route(
    "/employer-profiles/{profile_id}",
    methods=["PUT", "PATCH"],
    response_model=EmployerProfileResponse,
)
async def update_employer_profile(
    profile_id: int,
    profile_data: EmployerProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    if profile.user_id != current_user.id and not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.delete("/employer-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employer_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    if profile.user_id != current_user.id and not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to delete this profile")
    await db.delete(profile)
    await db.commit()


@router.get("/categories/", response_model=List[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Category))
    return result.scalars().all()


@router.get("/categories/{slug}", response_model=CategoryResponse)
async def get_category(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post(
    "/categories/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    existing = await db.execute(
        select(Category).where(Category.slug == category_data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category with this slug already exists")
    category = Category(**category_data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.put("/categories/{slug}", response_model=CategoryResponse)
async def update_category(
    slug: str,
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in category_data.model_dump().items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(category)
    await db.commit()


@router.get("/work-schedules/")
async def list_work_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkSchedule))
    items = result.scalars().all()
    return [{"id": w.id, "name": w.name, "slug": w.slug} for w in items]


@router.post(
    "/work-schedules/",
    status_code=status.HTTP_201_CREATED,
)
async def create_work_schedule(
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    slug = _slugify(name)
    ws = WorkSchedule(name=name, slug=slug)
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return {"id": ws.id, "name": ws.name, "slug": ws.slug}


@router.put("/work-schedules/{ws_id}")
async def update_work_schedule(
    ws_id: int,
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkSchedule).where(WorkSchedule.id == ws_id))
    ws = result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Work schedule not found")
    ws.name = name
    ws.slug = _slugify(name)
    await db.commit()
    await db.refresh(ws)
    return {"id": ws.id, "name": ws.name, "slug": ws.slug}


@router.delete("/work-schedules/{ws_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_schedule(
    ws_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkSchedule).where(WorkSchedule.id == ws_id))
    ws = result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Work schedule not found")
    await db.delete(ws)
    await db.commit()


@router.get("/work-formats/")
async def list_work_formats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkFormat))
    items = result.scalars().all()
    return [{"id": w.id, "name": w.name, "slug": w.slug} for w in items]


@router.post(
    "/work-formats/",
    status_code=status.HTTP_201_CREATED,
)
async def create_work_format(
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    slug = _slugify(name)
    wf = WorkFormat(name=name, slug=slug)
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return {"id": wf.id, "name": wf.name, "slug": wf.slug}


@router.put("/work-formats/{wf_id}")
async def update_work_format(
    wf_id: int,
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkFormat).where(WorkFormat.id == wf_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Work format not found")
    wf.name = name
    wf.slug = _slugify(name)
    await db.commit()
    await db.refresh(wf)
    return {"id": wf.id, "name": wf.name, "slug": wf.slug}


@router.delete("/work-formats/{wf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_format(
    wf_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkFormat).where(WorkFormat.id == wf_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Work format not found")
    await db.delete(wf)
    await db.commit()


@router.get("/work-experiences/")
async def list_work_experiences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkExperience))
    items = result.scalars().all()
    return [{"id": w.id, "name": w.name, "slug": w.slug} for w in items]


@router.post(
    "/work-experiences/",
    status_code=status.HTTP_201_CREATED,
)
async def create_work_experience(
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    slug = _slugify(name)
    we = WorkExperience(name=name, slug=slug)
    db.add(we)
    await db.commit()
    await db.refresh(we)
    return {"id": we.id, "name": we.name, "slug": we.slug}


@router.put("/work-experiences/{we_id}")
async def update_work_experience(
    we_id: int,
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkExperience).where(WorkExperience.id == we_id))
    we = result.scalar_one_or_none()
    if not we:
        raise HTTPException(status_code=404, detail="Work experience not found")
    we.name = name
    we.slug = _slugify(name)
    await db.commit()
    await db.refresh(we)
    return {"id": we.id, "name": we.name, "slug": we.slug}


@router.delete("/work-experiences/{we_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_experience(
    we_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkExperience).where(WorkExperience.id == we_id))
    we = result.scalar_one_or_none()
    if not we:
        raise HTTPException(status_code=404, detail="Work experience not found")
    await db.delete(we)
    await db.commit()
