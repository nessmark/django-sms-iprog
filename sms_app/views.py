"""
Views for SMS Project
IT 120 - Integrative Programming and Technologies

Implements request handling, validation workflows, TxtLink gateway interaction,
database logging, feedback alerts, and additional dashboard & contact features.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.conf import settings
from django.db.models import Count, Q

from .models import SMSMessage, Contact, QuickTemplate
from .forms import SMSComposeForm, ContactForm, QuickTemplateForm
from .services import TxtLinkService


def compose_sms(request):
    """
    Main View: SMS Composition and Dispatching.
    Handles the form display, input validation, TxtLink gateway communication,
    and displays appropriate success or error alerts to the user.
    """
    if request.method == 'POST':
        form = SMSComposeForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            message_text = form.cleaned_data['message']
            contact = form.cleaned_data.get('recipient_contact')

            # Calculate characters and segments
            segment_info = TxtLinkService.calculate_segments(message_text)

            # Send SMS via TxtLink Service
            gateway_result = TxtLinkService.send_sms(
                phone_number=phone_number,
                message=message_text
            )

            # Record in database log
            sms_record = SMSMessage.objects.create(
                phone_number=phone_number,
                message=message_text,
                status=gateway_result['status'],
                status_detail=gateway_result['detail'],
                gateway_message_id=gateway_result.get('message_id'),
                gateway_response=json.dumps(gateway_result.get('raw_response', {}), indent=2),
                character_count=segment_info['char_count'],
                segment_count=segment_info['segments'],
                is_simulation=gateway_result.get('is_simulation', False),
                error_message=gateway_result.get('error'),
                recipient_contact=contact
            )

            # Display appropriate feedback to user
            if gateway_result['success']:
                if gateway_result.get('is_simulation'):
                    messages.info(
                        request,
                        f"Demonstration Mode: Message submitted to simulated TxtLink gateway. "
                        f"Reference ID: {sms_record.gateway_message_id}. "
                        f"(Note: Message logged in system. Real SMS requires live API key)."
                    )
                else:
                    messages.success(
                        request,
                        f"Message successfully submitted to TxtLink gateway! "
                        f"Gateway Reference ID: {sms_record.gateway_message_id}. "
                        f"Status: Submitted (handset delivery will be fulfilled by carrier)."
                    )
                return redirect('sms_app:history')
            else:
                messages.error(
                    request,
                    f"SMS Submission Failed: {gateway_result['detail']}"
                )
        else:
            messages.error(request, "Please correct the errors in the form before proceeding.")
    else:
        # Prepopulate recipient if passed in query string (e.g. from contacts)
        initial_phone = request.GET.get('to', '')
        initial_msg = request.GET.get('text', '')
        form = SMSComposeForm(initial={
            'phone_number': initial_phone,
            'message': initial_msg
        })

    # Data for the view
    templates_list = QuickTemplate.objects.all()[:6]
    recent_messages = SMSMessage.objects.all()[:5]
    contacts_list = Contact.objects.all()

    context = {
        'form': form,
        'templates_list': templates_list,
        'recent_messages': recent_messages,
        'contacts_list': contacts_list,
        'is_simulation_mode': getattr(settings, 'TXTLINK_SIMULATION_MODE', False),
        'active_page': 'compose'
    }
    return render(request, 'sms_app/compose.html', context)


def history_list(request):
    """
    Displays the log of all sent SMS messages.
    Provides searching, status filtering, and inspection of gateway responses.
    """
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    messages_qs = SMSMessage.objects.all()

    if search_query:
        messages_qs = messages_qs.filter(
            Q(phone_number__icontains=search_query) |
            Q(message__icontains=search_query) |
            Q(gateway_message_id__icontains=search_query)
        )

    if status_filter:
        messages_qs = messages_qs.filter(status=status_filter)

    context = {
        'messages_list': messages_qs,
        'search_query': search_query,
        'status_filter': status_filter,
        'active_page': 'history'
    }
    return render(request, 'sms_app/history.html', context)


def message_detail(request, pk):
    """
    Displays full details of a single SMS transmission log,
    including raw TxtLink gateway response data.
    """
    msg = get_object_or_404(SMSMessage, pk=pk)
    return render(request, 'sms_app/detail.html', {'message_item': msg, 'active_page': 'history'})


def dashboard(request):
    """
    Provides an analytics dashboard showing sending stats, gateway status,
    and system distribution.
    """
    total_messages = SMSMessage.objects.count()
    submitted_count = SMSMessage.objects.filter(status='SUBMITTED').count()
    simulated_count = SMSMessage.objects.filter(status='SIMULATED').count()
    failed_count = SMSMessage.objects.filter(status='FAILED').count()
    delivered_count = SMSMessage.objects.filter(status='DELIVERED').count()
    total_contacts = Contact.objects.count()

    # Success rate (submitted + simulated + delivered vs total)
    effective_success = submitted_count + simulated_count + delivered_count
    success_rate = round((effective_success / total_messages * 100), 1) if total_messages > 0 else 0

    recent_activity = SMSMessage.objects.all()[:10]

    context = {
        'total_messages': total_messages,
        'submitted_count': submitted_count,
        'simulated_count': simulated_count,
        'failed_count': failed_count,
        'delivered_count': delivered_count,
        'total_contacts': total_contacts,
        'success_rate': success_rate,
        'recent_activity': recent_activity,
        'is_simulation_mode': getattr(settings, 'TXTLINK_SIMULATION_MODE', False),
        'active_page': 'dashboard'
    }
    return render(request, 'sms_app/dashboard.html', context)


def contacts_list(request):
    """
    Contact management page for adding and viewing saved numbers.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            messages.success(request, f"Contact '{contact.name}' successfully added.")
            return redirect('sms_app:contacts')
        else:
            messages.error(request, "Failed to add contact. Please check the entered fields.")
    else:
        form = ContactForm()

    all_contacts = Contact.objects.all()
    context = {
        'contacts': all_contacts,
        'form': form,
        'active_page': 'contacts'
    }
    return render(request, 'sms_app/contacts.html', context)


@require_POST
def delete_contact(request, pk):
    """
    Deletes a contact from the address book.
    """
    contact = get_object_or_404(Contact, pk=pk)
    name = contact.name
    contact.delete()
    messages.success(request, f"Contact '{name}' deleted.")
    return redirect('sms_app:contacts')


@require_POST
def clear_history(request):
    """
    Deletes all SMS logs.
    """
    count = SMSMessage.objects.count()
    SMSMessage.objects.all().delete()
    messages.info(request, f"Cleared {count} message records.")
    return redirect('sms_app:history')


def api_calculate_segments(request):
    """
    AJAX endpoint for real-time character counter and SMS segment calculation.
    """
    text = request.GET.get('text', '')
    data = TxtLinkService.calculate_segments(text)
    return JsonResponse(data)
