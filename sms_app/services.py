"""
TxtLink (TextLink) SMS Provider Service Module
IT 120 - Integrative Programming and Technologies

This module handles:
1. Formatting and sanitizing recipient phone numbers (E.164 and Philippine formats).
2. Estimating SMS character lengths and multi-part SMS segment calculations.
3. Securely dispatching SMS requests to the TxtLink REST API (https://textlinksms.com/api/send-sms).
4. Managing connection errors, timeouts, and provider response codes.
5. Providing a robust Demonstration / Simulation Mode when credentials or credits are pending.
6. Clearly distinguishing between gateway submission status and verified recipient delivery.
"""

import math
import re
import uuid
import requests
from django.conf import settings


class TxtLinkService:
    """
    Client for interacting with the TextLink SMS gateway API.
    """

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

    @classmethod
    def send_sms(cls, phone_number: str, message: str) -> dict:
        """
        Dispatches an SMS message through the TxtLink REST API.

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
        if not phone_number or not str(phone_number).strip():
            return {
                'success': False,
                'status': 'FAILED',
                'message_id': None,
                'detail': 'Recipient phone number is required.',
                'raw_response': {},
                'is_simulation': False,
                'error': 'Missing recipient phone number'
            }

        if not message or not str(message).strip():
            return {
                'success': False,
                'status': 'FAILED',
                'message_id': None,
                'detail': 'Message content cannot be empty.',
                'raw_response': {},
                'is_simulation': False,
                'error': 'Empty message body'
            }

        sanitized_phone = cls.sanitize_phone_number(phone_number)
        api_key = getattr(settings, 'TXTLINK_API_KEY', '').strip()
        api_url = getattr(settings, 'TXTLINK_API_URL', 'https://textlinksms.com/api/send-sms').strip()
        simulation_mode = getattr(settings, 'TXTLINK_SIMULATION_MODE', False)

        # 2. Check if running in Simulation Mode or API key is unconfigured
        is_mock_key = not api_key or api_key in ('your_txtlink_api_key_here', 'test_txtlink_api_key', 'test')

        if simulation_mode or is_mock_key:
            sim_id = f"TL-SIM-{uuid.uuid4().hex[:10].upper()}"
            reason = "Simulation mode enabled in configuration" if simulation_mode else "Placeholder/unconfigured API key detected"
            return {
                'success': True,
                'status': 'SIMULATED',
                'message_id': sim_id,
                'detail': (
                    f"SMS successfully simulated! Status: SUBMITTED to gateway sandbox. "
                    f"Reference ID: {sim_id}. ({reason})"
                ),
                'raw_response': {
                    'ok': True,
                    'mode': 'simulation',
                    'message_id': sim_id,
                    'recipient': sanitized_phone,
                    'note': 'Demonstration mode: SMS submission recorded without consuming external credits.'
                },
                'is_simulation': True,
                'error': None
            }

        # 3. Live Request via TxtLink REST API
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Django-SMS-Project/1.0 (IT120-IntegrativeProgramming)'
        }

        payload = {
            'phone_number': sanitized_phone,
            'text': message
        }

        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=12
            )

            # Parse JSON response
            try:
                data = response.json()
            except ValueError:
                data = {'raw_text': response.text}

            # TextLink standard response: status code 200/201 and data.get('ok') == True
            is_ok = response.status_code in (200, 201) and (
                data.get('ok') is True or
                data.get('status') in ('success', 'sent', 'queued') or
                'id' in data or
                'message_id' in data
            )

            if is_ok:
                msg_id = (
                    data.get('data', {}).get('id')
                    or data.get('id')
                    or data.get('message_id')
                    or f"TL-{uuid.uuid4().hex[:8].upper()}"
                )
                return {
                    'success': True,
                    'status': 'SUBMITTED',
                    'message_id': str(msg_id),
                    'detail': (
                        f"Message successfully submitted to TxtLink gateway. "
                        f"Status: Submitted (Gateway Reference: {msg_id}). "
                        f"Note: Final carrier delivery depends on network availability."
                    ),
                    'raw_response': data,
                    'is_simulation': False,
                    'error': None
                }
            else:
                # Gateway returned error status
                error_msg = (
                    data.get('message')
                    or data.get('error')
                    or f"Gateway returned HTTP {response.status_code}"
                )
                return {
                    'success': False,
                    'status': 'FAILED',
                    'message_id': None,
                    'detail': f"TxtLink Gateway error: {error_msg}",
                    'raw_response': data,
                    'is_simulation': False,
                    'error': str(error_msg)
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'status': 'FAILED',
                'message_id': None,
                'detail': "Request to TxtLink SMS gateway timed out (exceeded 12s). Please check your internet connection.",
                'raw_response': {'error': 'timeout'},
                'is_simulation': False,
                'error': 'Gateway timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'status': 'FAILED',
                'message_id': None,
                'detail': "Unable to reach TxtLink SMS servers. Network or DNS resolution failure.",
                'raw_response': {'error': 'connection_error'},
                'is_simulation': False,
                'error': 'Network connection failed'
            }
        except requests.exceptions.RequestException as exc:
            return {
                'success': False,
                'status': 'FAILED',
                'message_id': None,
                'detail': f"Unexpected communication error with TxtLink gateway: {str(exc)}",
                'raw_response': {'error': str(exc)},
                'is_simulation': False,
                'error': str(exc)
            }
