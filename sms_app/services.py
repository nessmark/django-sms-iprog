"""
SMS Provider Service Module
IT 120 - Integrative Programming and Technologies

This module handles:
1. Formatting and sanitizing recipient phone numbers (E.164 and Philippine formats).
2. Estimating SMS character lengths and multi-part SMS segment calculations.
3. Dispatching SMS requests to IPROG SMS (https://www.iprogsms.com), a Philippine gateway.
4. Managing connection errors, timeouts, and provider response codes.
5. Providing a robust Demonstration / Simulation Mode when credentials or credits are pending.
6. Clearly distinguishing between gateway submission status and verified recipient delivery.

Active provider - IPROG SMS:
- Philippine-only gateway with official Globe/TM/DITO routes on its shared sender.
- Student accounts get 5 FREE credits after verification, plus free daily test SMS.
- Sign up at https://www.iprogsms.com/register, then copy the token from API Settings.
- Smart/TNT numbers require an approved custom sender name.

Legacy provider - Textbelt (kept as a fallback reference):
- The shared key 'textbelt' sends 1 FREE SMS per day, but PH carriers commonly
  block unregistered foreign senders, so delivery to Philippine handsets is unreliable.
"""

import math
import re
import uuid
import requests
from django.conf import settings


# Keys that mean "not configured yet" -> caller should fall back to simulation.
_PLACEHOLDER_KEYS = {
    '',
    'your_textbelt_api_key_here',
    'test_textbelt_api_key',
    'test',
}


def _is_placeholder_key(api_key: str) -> bool:
    # NOTE: the literal 'textbelt' key is a real (free) key, so it is never a placeholder.
    key = (api_key or '').strip().lower()
    if key == 'textbelt':
        return False
    return key in _PLACEHOLDER_KEYS


def _is_placeholder_iprog_token(api_token: str) -> bool:
    token = (api_token or '').strip().lower()
    return token in _PLACEHOLDER_KEYS | {
        'your_iprog_api_token_here',
        'your_iprog_token_here',
        'test_iprog_token',
        'iprog_api_token',
    }


class BaseSMSService:
    """
    Shared helpers for the SMS service. Subclasses define:
        provider_name, provider_label, simulation_prefix
    and implement send_sms().
    """

    provider_name = 'base'
    provider_label = 'SMS provider'
    simulation_prefix = 'SMS-SIM'

    # ------------------------------------------------------------------
    # Segment + phone formatting
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_segments(text: str) -> dict:
        """
        Calculates character count and estimated SMS segment count.
        Standard GSM 7-bit: 160 characters for single SMS; 153 chars/segment for concatenated SMS.
        Unicode / UCS-2: 70 characters for single SMS; 67 chars/segment for concatenated.
        """
        char_count = len(text)
        if char_count == 0:
            return {'char_count': 0, 'segments': 0, 'is_unicode': False, 'remaining_in_segment': 160}

        # Check if non-ASCII characters exist (Unicode SMS)
        is_unicode = any(ord(c) > 127 for c in text)

        if not is_unicode:
            if char_count <= 160:
                segments = 1
                remaining = 160 - char_count
            else:
                segments = math.ceil(char_count / 153)
                remaining = (segments * 153) - char_count
        else:
            if char_count <= 70:
                segments = 1
                remaining = 70 - char_count
            else:
                segments = math.ceil(char_count / 67)
                remaining = (segments * 67) - char_count

        return {
            'char_count': char_count,
            'segments': segments,
            'is_unicode': is_unicode,
            'remaining_in_segment': remaining
        }

    @staticmethod
    def sanitize_phone_number(raw_phone: str) -> str:
        """
        Normalizes and sanitizes phone numbers into E.164 standard.
        Supports standard international formats (+63917..., +1555...)
        and converts Philippine national numbers (e.g., 09171234567 -> +639171234567).
        """
        if not raw_phone:
            return ""

        # Remove spaces, hyphens, parentheses, and dots
        cleaned = re.sub(r'[\s\-\(\)\.]', '', str(raw_phone).strip())

        # Philippine local mobile format starting with 09xxxxxxxxx (11 digits)
        if re.match(r'^09\d{9}$', cleaned):
            cleaned = '+63' + cleaned[1:]

        # Philippine local format starting with 9xxxxxxxxx (10 digits)
        elif re.match(r'^9\d{9}$', cleaned):
            cleaned = '+63' + cleaned

        # Missing leading + on international country codes (e.g. 639...)
        elif re.match(r'^639\d{9}$', cleaned):
            cleaned = '+' + cleaned

        # If already starts with + and digits, keep it
        elif cleaned.startswith('+') and cleaned[1:].isdigit():
            pass

        return cleaned

    # ------------------------------------------------------------------
    # Simulation support
    # ------------------------------------------------------------------
    @classmethod
    def is_simulation_active(cls) -> bool:
        """Whether the service would run in demonstration/simulation mode."""
        return bool(getattr(settings, 'SMS_SIMULATION_MODE', False))

    @classmethod
    def _simulated_result(cls, sanitized_phone: str, reason: str) -> dict:
        sim_id = f"{cls.simulation_prefix}-{uuid.uuid4().hex[:10].upper()}"
        return {
            'success': True,
            'status': 'SIMULATED',
            'message_id': sim_id,
            'detail': (
                f"SMS successfully simulated via {cls.provider_label}! Status: SUBMITTED to sandbox. "
                f"Reference ID: {sim_id}. ({reason})"
            ),
            'raw_response': {
                'ok': True,
                'provider': cls.provider_name,
                'mode': 'simulation',
                'message_id': sim_id,
                'recipient': sanitized_phone,
                'note': 'Demonstration mode: SMS submission recorded without consuming external credits.'
            },
            'is_simulation': True,
            'error': None
        }

    # ------------------------------------------------------------------
    # Validation + result helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _validation_error(phone_number: str, message: str):
        if not phone_number or not str(phone_number).strip():
            return 'Missing recipient phone number', 'Recipient phone number is required.'
        if not message or not str(message).strip():
            return 'Empty message body', 'Message content cannot be empty.'
        return None

    @staticmethod
    def _failed_result(detail: str, error: str, raw_response=None) -> dict:
        return {
            'success': False,
            'status': 'FAILED',
            'message_id': None,
            'detail': detail,
            'raw_response': raw_response or {},
            'is_simulation': False,
            'error': error
        }

    @classmethod
    def _exception_result(cls, exc: Exception) -> dict:
        if isinstance(exc, requests.exceptions.Timeout):
            return cls._failed_result(
                f"Request to {cls.provider_label} timed out (exceeded 12s). "
                f"Please check your internet connection.",
                'Gateway timeout',
                {'error': 'timeout'}
            )
        if isinstance(exc, requests.exceptions.ConnectionError):
            return cls._failed_result(
                f"Unable to reach {cls.provider_label} servers. "
                f"Network or DNS resolution failure.",
                'Network connection failed',
                {'error': 'connection_error'}
            )
        return cls._failed_result(
            f"Unexpected communication error with {cls.provider_label}: {exc}",
            str(exc),
            {'error': str(exc)}
        )


class IprogSMSService(BaseSMSService):
    """
    Client for the IPROG SMS API (https://www.iprogsms.com).

    Active provider for this project. IPROG is a Philippine SMS gateway that
    delivers through official Globe/TM/DITO routes using its shared sender.

    - Student accounts receive 5 free SMS credits after verification.
    - Free daily test SMS is also available (100-character limit, branded footer).
    - Smart/TNT numbers require an approved custom sender name.
    """

    provider_name = 'iprog'
    provider_label = 'IPROG SMS gateway'
    simulation_prefix = 'IPROG-SIM'

    @classmethod
    def is_simulation_active(cls) -> bool:
        if super().is_simulation_active():
            return True
        api_token = getattr(settings, 'IPROG_API_TOKEN', '')
        return _is_placeholder_iprog_token(api_token)

    @classmethod
    def _api_token(cls) -> str:
        return (getattr(settings, 'IPROG_API_TOKEN', '') or '').strip()

    @classmethod
    def send_sms(cls, phone_number: str, message: str) -> dict:
        """
        Dispatches an SMS message through the IPROG SMS REST API.

        Request (form-encoded POST):
            api_token, phone_number, message
        Response:
            {"status": 200, "message": "...", "message_id": "iSms-XHYBk"}

        Returns the same dictionary contract as the other services:
        {
            'success': bool,
            'status': str ('SUBMITTED', 'FAILED', or 'SIMULATED'),
            'message_id': str or None,
            'detail': str,
            'raw_response': dict or str,
            'is_simulation': bool,
            'error': str or None
        }
        """
        # 1. Validation of inputs
        invalid = cls._validation_error(phone_number, message)
        if invalid:
            error, detail = invalid
            return cls._failed_result(detail, error)

        sanitized_phone = cls.sanitize_phone_number(phone_number)

        # 2. Simulation mode or unconfigured token
        if cls.is_simulation_active():
            return cls._simulated_result(
                sanitized_phone,
                "Simulation mode enabled / IPROG API token missing or placeholder"
            )

        api_url = getattr(
            settings, 'IPROG_API_URL',
            'https://www.iprogsms.com/api/v1/sms_messages'
        ).strip()

        # IPROG examples use 639XXXXXXXXX (no leading '+').
        payload_phone = sanitized_phone[1:] if sanitized_phone.startswith('+') else sanitized_phone

        payload = {
            'api_token': cls._api_token(),
            'phone_number': payload_phone,
            'message': message,
        }

        # 3. Live request to IPROG (form-encoded POST)
        try:
            response = requests.post(api_url, data=payload, timeout=12)

            try:
                data = response.json()
            except ValueError:
                data = {'raw_text': response.text}

            status_value = data.get('status')
            accepted = (
                str(status_value) == '200'
                or status_value is True
                or str(status_value).lower() == 'success'
            )

            if response.status_code in (200, 201) and accepted and data.get('message_id'):
                msg_id = str(data['message_id'])
                detail = (
                    f"Message successfully submitted to IPROG SMS. "
                    f"Status: Submitted (Reference: {msg_id}). "
                    "Note: IPROG queues the message; final handset delivery depends on "
                    "network coverage and sender-name approval."
                )
                return {
                    'success': True,
                    'status': 'SUBMITTED',
                    'message_id': msg_id,
                    'detail': detail,
                    'raw_response': data,
                    'is_simulation': False,
                    'error': None
                }

            error_msg = (
                data.get('message')
                or data.get('error')
                or f"IPROG SMS returned HTTP {response.status_code}"
            )
            return cls._failed_result(
                f"IPROG SMS error: {error_msg}",
                str(error_msg),
                data
            )

        except requests.exceptions.RequestException as exc:
            return cls._exception_result(exc)

    @classmethod
    def check_status(cls, message_id: str) -> dict:
        """
        Queries IPROG for the delivery status of a previously sent message.

        GET /api/v1/sms_messages/status?api_token=...&message_id=...
        IPROG returns values such as "pending" and "completed".

        Returns:
        {
            'success': bool,             # False only when lookup fails or message FAILED
            'provider_status': str|None,
            'status': str|None,          # mapped app status: DELIVERED / SUBMITTED / FAILED
            'detail': str,
            'raw_response': dict,
            'error': str|None
        }
        """
        if not message_id or not str(message_id).strip():
            return {
                'success': False,
                'provider_status': None,
                'status': None,
                'detail': 'No gateway reference ID is available for a status lookup.',
                'raw_response': {},
                'error': 'Missing message id'
            }

        if cls.is_simulation_active():
            return {
                'success': False,
                'provider_status': None,
                'status': None,
                'detail': 'Delivery status lookup is unavailable in simulation mode.',
                'raw_response': {},
                'error': 'Simulation mode active'
            }

        status_url = getattr(
            settings, 'IPROG_STATUS_URL',
            'https://www.iprogsms.com/api/v1/sms_messages/status'
        ).strip()

        params = {
            'api_token': cls._api_token(),
            'message_id': str(message_id).strip(),
        }

        try:
            response = requests.get(status_url, params=params, timeout=12)
            try:
                data = response.json()
            except ValueError:
                data = {'raw_text': response.text}

            provider_status = str(
                data.get('message_status') or data.get('status') or ''
            ).strip().lower()

            if response.status_code == 200 and provider_status:
                mapped = {
                    'completed': 'DELIVERED',
                    'delivered': 'DELIVERED',
                    'failed': 'FAILED',
                    'error': 'FAILED',
                    'undelivered': 'FAILED',
                    'rejected': 'FAILED',
                    'pending': 'SUBMITTED',
                    'queued': 'SUBMITTED',
                    'processing': 'SUBMITTED',
                    'sent': 'SUBMITTED',
                    'submitted': 'SUBMITTED',
                }.get(provider_status, 'SUBMITTED')

                detail = f"IPROG delivery status: {provider_status.upper()}."
                if mapped == 'DELIVERED':
                    detail += ' Confirmed delivered by carrier.'
                elif mapped == 'FAILED':
                    detail += ' Carrier reported the message as not delivered.'
                else:
                    detail += ' Queued at the gateway; handset confirmation not yet available.'

                return {
                    'success': mapped != 'FAILED',
                    'provider_status': provider_status.upper(),
                    'status': mapped,
                    'detail': detail,
                    'raw_response': data,
                    'error': None
                }

            error_msg = (
                data.get('message')
                or data.get('error')
                or f"IPROG SMS returned HTTP {response.status_code}"
            )
            return {
                'success': False,
                'provider_status': None,
                'status': None,
                'detail': f"Status lookup error: {error_msg}",
                'raw_response': data,
                'error': str(error_msg)
            }

        except requests.exceptions.RequestException as exc:
            result = cls._exception_result(exc)
            return {
                'success': False,
                'provider_status': None,
                'status': None,
                'detail': result['detail'],
                'raw_response': result['raw_response'],
                'error': result['error']
            }


class TextbeltService(BaseSMSService):
    """
    Client for the Textbelt SMS API (https://textbelt.com).

    The shared key 'textbelt' sends 1 free SMS per day with no signup and no card.
    Create your own key at https://textbelt.com to buy additional credits.
    Numbers should be in E.164 format (e.g. +639171234567).
    """

    provider_name = 'textbelt'
    provider_label = 'Textbelt gateway'
    simulation_prefix = 'TB-SIM'

    @classmethod
    def is_simulation_active(cls) -> bool:
        if super().is_simulation_active():
            return True
        api_key = getattr(settings, 'TEXTBELT_API_KEY', 'textbelt')
        return _is_placeholder_key(api_key)

    @classmethod
    def send_sms(cls, phone_number: str, message: str) -> dict:
        """
        Dispatches an SMS message through the Textbelt REST API.

        Returns a dictionary structure:
        {
            'success': bool,
            'status': str ('SUBMITTED', 'FAILED', or 'SIMULATED'),
            'message_id': str or None,
            'detail': str,
            'raw_response': dict or str,
            'is_simulation': bool,
            'error': str or None
        }
        """
        # 1. Validation of inputs
        invalid = cls._validation_error(phone_number, message)
        if invalid:
            error, detail = invalid
            return cls._failed_result(detail, error)

        sanitized_phone = cls.sanitize_phone_number(phone_number)
        api_key = (getattr(settings, 'TEXTBELT_API_KEY', 'textbelt') or '').strip() or 'textbelt'
        api_url = getattr(settings, 'TEXTBELT_API_URL', 'https://textbelt.com/text').strip()

        # 2. Simulation mode or unconfigured key
        if cls.is_simulation_active():
            return cls._simulated_result(sanitized_phone, "Simulation mode enabled / placeholder key detected")

        # 3. Live request to Textbelt (form-encoded POST)
        payload = {
            'phone': sanitized_phone,
            'message': message,
            'key': api_key,
        }

        try:
            response = requests.post(api_url, data=payload, timeout=12)

            try:
                data = response.json()
            except ValueError:
                data = {'raw_text': response.text}

            if response.status_code in (200, 201) and data.get('success') is True:
                msg_id = data.get('textId') or data.get('text_id') or f"TB-{uuid.uuid4().hex[:8].upper()}"
                quota = data.get('quotaRemaining')
                detail = (
                    f"Message successfully submitted to Textbelt. "
                    f"Status: Submitted (Reference: {msg_id}). "
                )
                if quota is not None:
                    detail += f"Quota remaining: {quota}. "
                detail += "Note: Final carrier delivery depends on network availability."
                return {
                    'success': True,
                    'status': 'SUBMITTED',
                    'message_id': str(msg_id),
                    'detail': detail,
                    'raw_response': data,
                    'is_simulation': False,
                    'error': None
                }

            error_msg = (
                data.get('error')
                or data.get('message')
                or f"Textbelt returned HTTP {response.status_code}"
            )
            return cls._failed_result(
                f"Textbelt error: {error_msg}",
                str(error_msg),
                data
            )

        except requests.exceptions.RequestException as exc:
            return cls._exception_result(exc)

    @classmethod
    def check_status(cls, message_id: str) -> dict:
        """
        Queries Textbelt for the delivery status of a previously sent message.

        Uses GET https://textbelt.com/status/<textId>, which returns one of:
        DELIVERED, SENT, SENDING, FAILED, UNKNOWN.

        Returns:
        {
            'success': bool,            # False only when lookup fails or carrier reports FAILED
            'provider_status': str|None,
            'status': str|None,          # mapped app status: DELIVERED / SUBMITTED / FAILED
            'detail': str,
            'raw_response': dict,
            'error': str|None
        }
        """
        if not message_id or not str(message_id).strip():
            return {
                'success': False,
                'provider_status': None,
                'status': None,
                'detail': 'No gateway reference ID is available for a status lookup.',
                'raw_response': {},
                'error': 'Missing message id'
            }

        base = getattr(settings, 'TEXTBELT_STATUS_URL', 'https://textbelt.com/status').rstrip('/')
        url = f"{base}/{str(message_id).strip()}"

        try:
            response = requests.get(url, timeout=12)
            try:
                data = response.json()
            except ValueError:
                data = {'raw_text': response.text}

            if response.status_code == 200 and isinstance(data, dict) and data.get('status'):
                provider_status = str(data['status']).upper()
                mapped = {
                    'DELIVERED': 'DELIVERED',
                    'SENT': 'SUBMITTED',
                    'SENDING': 'SUBMITTED',
                    'FAILED': 'FAILED',
                    'UNKNOWN': 'SUBMITTED',
                }.get(provider_status, 'SUBMITTED')

                detail = f"Textbelt delivery status: {provider_status}."
                if provider_status == 'DELIVERED':
                    detail += ' Confirmed delivered by carrier.'
                elif provider_status in ('SENT', 'SENDING'):
                    detail += ' Handed to carrier; handset confirmation not yet available.'
                elif provider_status == 'FAILED':
                    detail += ' Carrier reported the message as not delivered.'
                elif provider_status == 'UNKNOWN':
                    detail += ' Carrier delivery could not be confirmed.'

                return {
                    'success': provider_status != 'FAILED',
                    'provider_status': provider_status,
                    'status': mapped,
                    'detail': detail,
                    'raw_response': data,
                    'error': None
                }

            error_msg = (
                data.get('error')
                or data.get('message')
                or f"Textbelt returned HTTP {response.status_code}"
            )
            return {
                'success': False,
                'provider_status': None,
                'status': None,
                'detail': f"Status lookup error: {error_msg}",
                'raw_response': data,
                'error': str(error_msg)
            }

        except requests.exceptions.RequestException as exc:
            result = cls._exception_result(exc)
            return {
                'success': False,
                'provider_status': None,
                'status': None,
                'detail': result['detail'],
                'raw_response': result['raw_response'],
                'error': result['error']
            }
