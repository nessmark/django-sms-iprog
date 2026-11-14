from django.db import models
from django.utils import timezone


class Contact(models.Model):
    """
    Model representing saved recipient contacts for quick selection.
    """
    name = models.CharField(max_length=100, help_text="Full Name or Nickname")
    phone_number = models.CharField(
        max_length=25,
        help_text="Phone number in international format (+639... or 09...)"
    )
    email = models.EmailField(blank=True, null=True, help_text="Optional contact email")
    notes = models.CharField(max_length=255, blank=True, help_text="Relationship or brief note")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'

    def __str__(self):
        return f"{self.name} ({self.phone_number})"


class SMSMessage(models.Model):
    """
    Model to store SMS sending logs, statuses, and gateway responses.
    Demonstrates message history and status tracking (Submission vs Delivery).
    """
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted to Gateway'),
        ('DELIVERED', 'Confirmed Delivered'),
        ('FAILED', 'Failed / Rejected'),
        ('SIMULATED', 'Simulated (Demo Mode)'),
    ]

    phone_number = models.CharField(
        max_length=25,
        help_text="Recipient phone number (e.g. +639171234567)"
    )
    message = models.TextField(help_text="Message body content")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SUBMITTED',
        help_text="Current dispatch status"
    )
    status_detail = models.CharField(
        max_length=255,
        blank=True,
        help_text="Detailed status description from gateway or error feedback"
    )
    gateway_message_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Message ID returned by TxtLink"
    )
    gateway_response = models.TextField(
        blank=True,
        help_text="Raw or formatted response payload from the SMS provider"
    )
    character_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of characters in the message"
    )
    segment_count = models.PositiveIntegerField(
        default=1,
        help_text="Estimated SMS segments (160 chars / segment standard)"
    )
    is_simulation = models.BooleanField(
        default=False,
        help_text="Indicates whether this dispatch was run in simulation mode"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if the dispatch failed"
    )
    recipient_contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        help_text="Linked contact if selected from address book"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Timestamp when message was submitted"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'SMS Message Log'
        verbose_name_plural = 'SMS Message Logs'

    def __str__(self):
        return f"To: {self.phone_number} | Status: {self.get_status_display()} | Sent: {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def status_badge_class(self):
        """Returns Bootstrap badge class according to status"""
        badge_map = {
            'SUBMITTED': 'bg-primary',
            'DELIVERED': 'bg-success',
            'FAILED': 'bg-danger',
            'SIMULATED': 'bg-info text-dark',
        }
        return badge_map.get(self.status, 'bg-secondary')


class QuickTemplate(models.Model):
    """
    Predefined SMS templates for rapid composition.
    """
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=50, default='General')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title
