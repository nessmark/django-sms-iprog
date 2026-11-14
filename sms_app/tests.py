"""
Unit & Integration Test Suite for SMS Project
IT 120 - Integrative Programming and Technologies

Tests all cases required in Section VI (Testing Procedures):
1. Valid phone number and message submission.
2. Empty phone number validation rejection.
3. Empty message validation rejection.
4. Invalid phone number format handling.
5. Incorrect or missing API credentials handling without exposing secrets.
6. Provider or network connection error handling.
7. Submission status vs delivery verification distinction.
8. Live character count and SMS segment calculation.
9. Contact management CRUD operations.
10. Dashboard and message history view accessibility.
"""

from unittest.mock import patch, MagicMock
import requests
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from .models import SMSMessage, Contact, QuickTemplate
from .services import TxtLinkService
from .forms import SMSComposeForm, ContactForm


class TxtLinkServiceUnitTests(TestCase):
    """
    Direct unit tests for the TxtLinkService helper methods and API caller.
    """

    def test_phone_sanitization_philippine_mobile(self):
        """Test conversion of Philippine national formats (09... and 9...) to E.164 (+639...)"""
        self.assertEqual(TxtLinkService.sanitize_phone_number("09171234567"), "+639171234567")
        self.assertEqual(TxtLinkService.sanitize_phone_number("0918-987-6543"), "+639189876543")
        self.assertEqual(TxtLinkService.sanitize_phone_number("+63 917 123 4567"), "+639171234567")
        self.assertEqual(TxtLinkService.sanitize_phone_number("639171234567"), "+639171234567")

    def test_phone_sanitization_international(self):
        """Test preservation of international E.164 numbers"""
        self.assertEqual(TxtLinkService.sanitize_phone_number("+1 (555) 123-4567"), "+15551234567")
        self.assertEqual(TxtLinkService.sanitize_phone_number("+44 20 7946 0991"), "+442079460991")

    def test_character_and_segment_calculation(self):
        """Test accurate SMS segment calculation (160 standard GSM vs concatenated 153)"""
        short_msg = "Hello World"
        calc = TxtLinkService.calculate_segments(short_msg)
        self.assertEqual(calc['char_count'], 11)
        self.assertEqual(calc['segments'], 1)
        self.assertFalse(calc['is_unicode'])

        # Exactly 160 characters
        exact_msg = "A" * 160
        calc_exact = TxtLinkService.calculate_segments(exact_msg)
        self.assertEqual(calc_exact['char_count'], 160)
        self.assertEqual(calc_exact['segments'], 1)

        # 161 characters -> 2 segments (153 chars/segment)
        long_msg = "A" * 161
        calc_long = TxtLinkService.calculate_segments(long_msg)
        self.assertEqual(calc_long['segments'], 2)

    def test_unicode_segment_calculation(self):
        """Test Unicode SMS character limit (70 chars per segment)"""
        unicode_msg = "Kamusta mundo! 👋🇵🇭"
        calc = TxtLinkService.calculate_segments(unicode_msg)
        self.assertTrue(calc['is_unicode'])
        self.assertEqual(calc['segments'], 1)

    @override_settings(TXTLINK_SIMULATION_MODE=True)
    def test_simulation_mode_dispatch(self):
        """Test that simulation mode successfully produces a mock gateway response"""
        result = TxtLinkService.send_sms("+639171234567", "Testing simulation mode")
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'SIMULATED')
        self.assertTrue(result['is_simulation'])
        self.assertIn("TL-SIM-", result['message_id'])

    @override_settings(TXTLINK_SIMULATION_MODE=False, TXTLINK_API_KEY="valid_test_key")
    @patch('sms_app.services.requests.post')
    def test_live_gateway_success_response(self, mock_post):
        """
        Test case: Successful provider response.
        Ensures that status is SUBMITTED and does not falsely claim handset delivery.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'data': {'id': 'TL-12345-ABC', 'status': 'queued'}
        }
        mock_post.return_value = mock_response

        result = TxtLinkService.send_sms("+639171234567", "Live test payload")

        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'SUBMITTED')
        self.assertEqual(result['message_id'], 'TL-12345-ABC')
        self.assertIn("Status: Submitted", result['detail'])
        # Verify provider called with correct bearer token
        mock_post.assert_called_once()
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['Authorization'], 'Bearer valid_test_key')

    @override_settings(TXTLINK_SIMULATION_MODE=False, TXTLINK_API_KEY="invalid_key")
    @patch('sms_app.services.requests.post')
    def test_missing_or_incorrect_credentials(self, mock_post):
        """
        Test case: Missing or incorrect credentials.
        Application handles error without exposing secrets.
        """
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'ok': False,
            'message': 'Invalid API Key provided'
        }
        mock_post.return_value = mock_response

        result = TxtLinkService.send_sms("+639171234567", "Security test")

        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'FAILED')
        self.assertIn("Invalid API Key", result['detail'])
        # Verify secret key itself was not leaked in output
        self.assertNotIn("invalid_key", result['detail'])

    @override_settings(TXTLINK_SIMULATION_MODE=False, TXTLINK_API_KEY="valid_key")
    @patch('sms_app.services.requests.post')
    def test_network_connection_error(self, mock_post):
        """
        Test case: Provider or network error.
        Application handles connection loss cleanly.
        """
        mock_post.side_effect = requests.exceptions.ConnectionError("Failed to resolve host")

        result = TxtLinkService.send_sms("+639171234567", "Network test")

        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'FAILED')
        self.assertIn("Network or DNS resolution failure", result['detail'])

    @override_settings(TXTLINK_SIMULATION_MODE=False, TXTLINK_API_KEY="valid_key")
    @patch('sms_app.services.requests.post')
    def test_network_timeout_error(self, mock_post):
        """
        Test case: Network timeout handling.
        """
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        result = TxtLinkService.send_sms("+639171234567", "Timeout test")

        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'FAILED')
        self.assertIn("timed out", result['detail'])


class FormValidationTests(TestCase):
    """
    Tests for SMSComposeForm and ContactForm input validation.
    """

    def test_valid_form_data(self):
        """Test valid recipient and message input"""
        form = SMSComposeForm(data={
            'phone_number': '09171234567',
            'message': 'Valid test message content.'
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone_number'], '+639171234567')

    def test_empty_phone_number_rejected(self):
        """Test case: Empty phone number rejected with validation error"""
        form = SMSComposeForm(data={
            'phone_number': '',
            'message': 'Message with no recipient'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)

    def test_empty_message_rejected(self):
        """Test case: Empty message rejected with validation error"""
        form = SMSComposeForm(data={
            'phone_number': '+639171234567',
            'message': '   '
        })
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)

    def test_invalid_phone_number_format(self):
        """Test case: Invalid phone number format (letters / too short) rejected"""
        invalid_numbers = ['abc12345', '123', 'invalid-phone-num', '++63917123456789012345']
        for bad_num in invalid_numbers:
            form = SMSComposeForm(data={
                'phone_number': bad_num,
                'message': 'Hello'
            })
            self.assertFalse(form.is_valid(), f"Expected {bad_num} to be invalid")
            self.assertIn('phone_number', form.errors)


class ViewIntegrationTests(TestCase):
    """
    Integration tests for user interface, routes, and submission workflows.
    """

    def setUp(self):
        self.client = Client()
        self.contact = Contact.objects.create(
            name="Test Instructor",
            phone_number="+639170000000",
            email="instructor@example.com"
        )
        self.template = QuickTemplate.objects.create(
            title="Class Advisory",
            category="Notice",
            content="This is a test advisory."
        )

    def test_compose_view_get(self):
        """Test GET request to compose view loads successfully with 200 OK"""
        response = self.client.get(reverse('sms_app:compose'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send SMS Message")
        self.assertContains(response, "Interactive Recipient Handset Preview")

    @override_settings(TXTLINK_SIMULATION_MODE=True)
    def test_compose_view_post_success(self):
        """
        Test successful POST request submitting SMS.
        Verifies redirection to history and creation of SMSMessage database record.
        """
        post_data = {
            'phone_number': '09171234567',
            'message': 'Hello from automated Django test!'
        }
        response = self.client.post(reverse('sms_app:compose'), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SMSMessage.objects.count(), 1)

        msg = SMSMessage.objects.first()
        self.assertEqual(msg.phone_number, '+639171234567')
        self.assertEqual(msg.status, 'SIMULATED')
        self.assertTrue(msg.is_simulation)

    def test_compose_view_post_empty_fails(self):
        """Test POST request with empty data returns form errors and 200 without creating log"""
        response = self.client.post(reverse('sms_app:compose'), {'phone_number': '', 'message': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SMSMessage.objects.count(), 0)
        self.assertContains(response, "Please correct the errors in the form")

    def test_history_list_view(self):
        """Test SMS history view displays logs correctly"""
        SMSMessage.objects.create(
            phone_number="+639179999999",
            message="Test history message",
            status="SUBMITTED",
            gateway_message_id="TL-TEST-99"
        )
        response = self.client.get(reverse('sms_app:history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "+639179999999")
        self.assertContains(response, "TL-TEST-99")

    def test_message_detail_view(self):
        """Test message detail view displays payload and metadata"""
        msg = SMSMessage.objects.create(
            phone_number="+639178888888",
            message="Detailed test log",
            status="SUBMITTED",
            gateway_message_id="TL-TEST-88",
            gateway_response='{"ok": true, "msg": "queued"}'
        )
        response = self.client.get(reverse('sms_app:detail', kwargs={'pk': msg.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "+639178888888")
        self.assertContains(response, "TL-TEST-88")

    def test_dashboard_view(self):
        """Test analytics dashboard computes metrics properly"""
        SMSMessage.objects.create(phone_number="+639171111111", message="M1", status="SUBMITTED")
        SMSMessage.objects.create(phone_number="+639172222222", message="M2", status="FAILED")

        response = self.client.get(reverse('sms_app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SMS Gateway Analytics Dashboard")
        self.assertEqual(response.context['total_messages'], 2)
        self.assertEqual(response.context['submitted_count'], 1)
        self.assertEqual(response.context['failed_count'], 1)

    def test_contact_management(self):
        """Test creating and deleting contacts in address book"""
        # Create contact
        response = self.client.post(reverse('sms_app:contacts'), {
            'name': 'Prof. John Doe',
            'phone_number': '09195551234',
            'email': 'jdoe@univ.edu.ph',
            'notes': 'Adviser'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        new_contact = Contact.objects.filter(name='Prof. John Doe').first()
        self.assertIsNotNone(new_contact)
        self.assertEqual(new_contact.phone_number, '+639195551234')

        # Delete contact
        del_response = self.client.post(
            reverse('sms_app:delete_contact', kwargs={'pk': new_contact.pk}),
            follow=True
        )
        self.assertEqual(del_response.status_code, 200)
        self.assertFalse(Contact.objects.filter(name='Prof. John Doe').exists())

    def test_api_calculate_segments(self):
        """Test the AJAX API endpoint for live segment calculation"""
        response = self.client.get(reverse('sms_app:api_calculate_segments'), {'text': 'Hello World'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['char_count'], 11)
        self.assertEqual(data['segments'], 1)
