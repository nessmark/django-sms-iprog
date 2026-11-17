from django.urls import path
from . import views

app_name = 'sms_app'

urlpatterns = [
    # Core SMS composition
    path('', views.compose_sms, name='compose'),

    # SMS history and details
    path('history/', views.history_list, name='history'),
    path('history/<int:pk>/', views.message_detail, name='detail'),
    path('history/<int:pk>/status/', views.check_delivery_status, name='check_status'),
    path('history/clear/', views.clear_history, name='clear_history'),

    # Dashboard and analytics
    path('dashboard/', views.dashboard, name='dashboard'),

    # Contacts management
    path('contacts/', views.contacts_list, name='contacts'),
    path('contacts/<int:pk>/delete/', views.delete_contact, name='delete_contact'),

    # Live API utility
    path('api/calculate-segments/', views.api_calculate_segments, name='api_calculate_segments'),
]
