import hashlib
import hmac
import time
import requests
from django.conf import settings


class DushanbeCityPayment:
    PROD_URL = "https://api.express-pay.by/v1"
    SANDBOX_URL = "https://sandbox-api.express-pay.by/v1"

    def __init__(self):
        self.token = getattr(settings, 'EXPRESS_PAY_TOKEN', '')
        self.secret = getattr(settings, 'EXPRESS_PAY_SECRET', '')
        self.merchant_id = getattr(settings, 'EXPRESS_PAY_MERCHANT_ID', '')
        self.frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        sandbox = getattr(settings, 'EXPRESS_PAY_SANDBOX', True)
        self.base_url = self.SANDBOX_URL if sandbox else self.PROD_URL

    def _generate_signature(self, params):
        sorted_values = ''.join(str(v) for v in sorted(params.values(), key=lambda x: str(x)))
        return hmac.new(
            self.secret.encode('utf-8'),
            sorted_values.encode('utf-8'),
            hashlib.sha1
        ).hexdigest().upper()

    def create_invoice(self, user, amount, description, subscription_id):
        account_no = f"careerhub_{user.id}_{subscription_id}_{int(time.time())}"

        params = {
            'Token': self.token,
            'AccountNo': account_no,
            'Amount': str(amount),
            'Currency': '933',
            'Info': description,
            'SuccessRedirectUrl': f'{self.frontend_url}/pricing?status=success',
            'FailRedirectUrl': f'{self.frontend_url}/pricing?status=failed',
        }

        params['Signature'] = self._generate_signature(params)

        try:
            response = requests.post(
                f'{self.base_url}/invoices',
                data=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return {
                'success': True,
                'invoice_no': data.get('InvoiceNo'),
                'redirect_url': data.get('RedirectUrl'),
                'account_no': account_no,
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
            }

    def check_status(self, invoice_no):
        params = {
            'Token': self.token,
            'InvoiceNo': invoice_no,
        }

        params['Signature'] = self._generate_signature(params)

        try:
            response = requests.get(
                f'{self.base_url}/invoices/{invoice_no}/status',
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return {
                'success': True,
                'status': data.get('Status'),
                'data': data,
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
            }

    def verify_webhook_signature(self, data):
        received_signature = data.get('Signature', '')
        params_to_verify = {k: v for k, v in data.items() if k != 'Signature'}
        expected_signature = self._generate_signature(params_to_verify)
        return hmac.compare_digest(received_signature, expected_signature)


payment_service = DushanbeCityPayment()
