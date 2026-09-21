import os
import hmac
import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx


EXPRESS_PAY_BASE_URL = os.environ.get(
    "EXPRESS_PAY_BASE_URL", "https://sandbox.webpay.tj"
)
EXPRESS_PAY_MERCHANT_ID = os.environ.get("EXPRESS_PAY_MERCHANT_ID", "")
EXPRESS_PAY_SECRET_KEY = os.environ.get("EXPRESS_PAY_SECRET_KEY", "")
EXPRESS_PAY_RETURN_URL = os.environ.get("EXPRESS_PAY_RETURN_URL", "http://localhost:3000/payments/callback")
EXPRESS_PAY_CANCEL_URL = os.environ.get("EXPRESS_PAY_CANCEL_URL", "http://localhost:3000/payments/cancel")
EXPRESS_PAY_CALLBACK_URL = os.environ.get("EXPRESS_PAY_CALLBACK_URL", "http://localhost:8000/api/payments/webhook/")

WEBHOOK_SECRET = os.environ.get("EXPRESS_PAY_WEBHOOK_SECRET", EXPRESS_PAY_SECRET_KEY)


def generate_hmac_sha1(secret: str, message: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha1,
    ).hexdigest()


class DushanbeCityPayment:
    def __init__(
        self,
        merchant_id: str = EXPRESS_PAY_MERCHANT_ID,
        secret_key: str = EXPRESS_PAY_SECRET_KEY,
        base_url: str = EXPRESS_PAY_BASE_URL,
        return_url: str = EXPRESS_PAY_RETURN_URL,
        cancel_url: str = EXPRESS_PAY_CANCEL_URL,
        callback_url: str = EXPRESS_PAY_CALLBACK_URL,
    ):
        self.merchant_id = merchant_id
        self.secret_key = secret_key
        self.base_url = base_url.rstrip("/")
        self.return_url = return_url
        self.cancel_url = cancel_url
        self.callback_url = callback_url

    def generate_invoice_number(self) -> str:
        timestamp = int(time.time())
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"CH-{timestamp}-{unique_id}"

    def _generate_signature(self, data: str) -> str:
        return generate_hmac_sha1(self.secret_key, data)

    async def create_invoice(
        self,
        amount: int,
        invoice_no: Optional[str] = None,
        description: str = "CareerHub Subscription",
        email: str = "",
        phone: str = "",
        extra_data: Optional[dict] = None,
    ) -> dict:
        if not invoice_no:
            invoice_no = self.generate_invoice_number()

        signature_string = f"{self.merchant_id}{invoice_no}{amount}{description}"
        signature = self._generate_signature(signature_string)

        payload = {
            "merchantId": self.merchant_id,
            "invoiceNo": invoice_no,
            "amount": amount,
            "description": description,
            "returnUrl": self.return_url,
            "cancelUrl": self.cancel_url,
            "callbackUrl": self.callback_url,
            "signature": signature,
        }

        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        if extra_data:
            payload["extraData"] = extra_data

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/api/v1/invoices",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                result = resp.json()

            invoice_url = result.get("invoiceUrl", "")
            payment_id = result.get("paymentId", "")

            return {
                "success": True,
                "invoice_no": invoice_no,
                "invoice_url": invoice_url,
                "payment_id": payment_id,
                "amount": amount,
                "status": "created",
            }

        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "invoice_no": invoice_no,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "invoice_no": invoice_no,
            }

    async def check_status(self, invoice_no: str) -> dict:
        signature_string = f"{self.merchant_id}{invoice_no}"
        signature = self._generate_signature(signature_string)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/invoices/{invoice_no}",
                    params={
                        "merchantId": self.merchant_id,
                        "signature": signature,
                    },
                )
                resp.raise_for_status()
                result = resp.json()

            return {
                "success": True,
                "invoice_no": invoice_no,
                "status": result.get("status", "unknown"),
                "paid_at": result.get("paidAt"),
                "payment_method": result.get("paymentMethod", ""),
                "amount": result.get("amount"),
            }

        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    @staticmethod
    def verify_webhook_signature(payload: dict, secret: str = WEBHOOK_SECRET) -> bool:
        received_signature = payload.get("signature", "")
        if not received_signature:
            return False

        invoice_no = payload.get("invoiceNo", "")
        status = payload.get("status", "")
        amount = payload.get("amount", "")

        signature_string = f"{invoice_no}{status}{amount}"
        expected_signature = generate_hmac_sha1(secret, signature_string)

        return hmac.compare_digest(received_signature, expected_signature)

    @staticmethod
    def parse_webhook_payload(payload: dict) -> dict:
        return {
            "invoice_no": payload.get("invoiceNo", ""),
            "status": payload.get("status", ""),
            "amount": payload.get("amount", 0),
            "payment_method": payload.get("paymentMethod", ""),
            "paid_at": payload.get("paidAt", ""),
            "payment_id": payload.get("paymentId", ""),
            "signature": payload.get("signature", ""),
        }


payment_service = DushanbeCityPayment()
