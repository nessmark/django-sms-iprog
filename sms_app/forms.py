"""
Forms for SMS Project
IT 120 - Integrative Programming and Technologies

Implements form definitions, input sanitization, and robust error validation
for SMS composition, contact management, and quick templates.
"""

import re
from django import forms
from .models import Contact, SMSMessage, QuickTemplate
from .services import TextbeltService


class SMSComposeForm(forms.Form):
    """
    Form for composing and sending an SMS message.
    Satisfies requirements:
    - Recipient phone number field
    - Message input field
    - Comprehensive input validation
    """
    phone_number = forms.CharField(
        label="Recipient Phone Number",
        max_length=25,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'e.g. +639171234567 or 09171234567',
            'id': 'id_phone_number',
            'autocomplete': 'tel',
        }),
        help_text="Enter number with country code (e.g. +639...) or Philippine mobile format (09...)"
    )

    message = forms.CharField(
        label="SMS Message",
        max_length=1600,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Type your message here...',
            'id': 'id_message',
        }),
        help_text="Standard SMS is 160 characters (GSM-7). Messages exceeding 160 characters are sent in multiple segments."
    )

    recipient_contact = forms.ModelChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        empty_label="-- Or select from saved contacts --",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_contact_selector'
        }),
        help_text="Optional: Select a saved contact from your address book."
    )

    def clean_phone_number(self):
        raw_number = self.cleaned_data.get('phone_number', '').strip()

        if not raw_number:
            raise forms.ValidationError("Recipient phone number cannot be empty.")

        # Strip whitespace, dashes, parentheses
        sanitized = TextbeltService.sanitize_phone_number(raw_number)

        # Basic international E.164 phone regex: + followed by 7 to 15 digits
        e164_pattern = r'^\+[1-9]\d{6,14}$'

        if not re.match(e164_pattern, sanitized):
            raise forms.ValidationError(
                "Invalid phone number format. Please provide a valid phone number, "
                "such as +639171234567, +15551234567, or Philippine mobile format 09171234567."
            )

        return sanitized

    def clean_message(self):
        text = self.cleaned_data.get('message', '').strip()

        if not text:
            raise forms.ValidationError("Message content cannot be blank or contain only whitespace.")

        if len(text) > 1600:
            raise forms.ValidationError(
                f"Message exceeds maximum allowed length of 1600 characters (current: {len(text)})."
            )

        return text


class ContactForm(forms.ModelForm):
    """
    Form for adding and editing saved recipient contacts.
    """
    class Meta:
        model = Contact
        fields = ['name', 'phone_number', 'email', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name or Nickname'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +639171234567 or 09171234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional notes or department'}),
        }

    def clean_phone_number(self):
        raw_number = self.cleaned_data.get('phone_number', '').strip()
        if not raw_number:
            raise forms.ValidationError("Phone number is required.")

        sanitized = TextbeltService.sanitize_phone_number(raw_number)
        e164_pattern = r'^\+[1-9]\d{6,14}$'

        if not re.match(e164_pattern, sanitized):
            raise forms.ValidationError(
                "Invalid phone number format. Please use E.164 format (+639...) or 09..."
            )
        return sanitized


class QuickTemplateForm(forms.ModelForm):
    """
    Form for creating new quick message templates.
    """
    class Meta:
        model = QuickTemplate
        fields = ['title', 'category', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Template Title (e.g. Meeting Alert)'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category (e.g. Alerts, General)'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Template message text...'}),
        }
