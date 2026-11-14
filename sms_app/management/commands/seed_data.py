from django.core.management.base import BaseCommand
from sms_app.models import Contact, QuickTemplate


class Command(BaseCommand):
    help = 'Seeds initial sample contacts and templates for testing and demonstration'

    def handle(self, *args, **options):
        # Seed Contacts
        contacts_data = [
            {
                'name': 'Joshua Tubo (Instructor)',
                'phone_number': '+639171234567',
                'email': 'joshuatubo4@gmail.com',
                'notes': 'IT 120 Course Instructor'
            },
            {
                'name': 'College Dean / IT Dept',
                'phone_number': '+639189876543',
                'email': 'itdept@univ.edu.ph',
                'notes': 'College of Information Technology'
            },
            {
                'name': 'Student Council President',
                'phone_number': '+639205551234',
                'email': 'council@univ.edu.ph',
                'notes': 'Campus Student Council'
            }
        ]

        created_contacts = 0
        for item in contacts_data:
            contact, created = Contact.objects.get_or_create(
                phone_number=item['phone_number'],
                defaults=item
            )
            if created:
                created_contacts += 1

        # Seed Quick Templates
        templates_data = [
            {
                'title': 'Course Notice',
                'category': 'Academic',
                'content': 'Good day! Please be informed that our IT 120 class has updated lecture slides available on the portal.'
            },
            {
                'title': 'Assignment Reminder',
                'category': 'Deadlines',
                'content': 'Reminder: The IT 120 SMS Gateway Django Project submission deadline is approaching. Please ensure all tests pass.'
            },
            {
                'title': 'OTP Verification',
                'category': 'Security',
                'content': 'Your one-time security verification code is 849201. It is valid for 5 minutes. Never share this code.'
            },
            {
                'title': 'Laboratory Alert',
                'category': 'Advisory',
                'content': 'Advisory: The computer laboratory session today will cover external REST API integration and environment security.'
            }
        ]

        created_templates = 0
        for item in templates_data:
            tmpl, created = QuickTemplate.objects.get_or_create(
                title=item['title'],
                defaults=item
            )
            if created:
                created_templates += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded database: {created_contacts} contacts and {created_templates} templates."
            )
        )
