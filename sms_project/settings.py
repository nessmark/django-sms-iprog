"""
Django settings for sms_project project.

Built for IT 120 - Integrative Programming and Technologies
Assignment: Build a Django Application for Sending SMS using the IPROG SMS API.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-33io&%1iuk*v@@#p)bjz^$14xmhsi9^w(c6y$%2#l40ij0qc6u'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

# Allowed hosts parsed from comma-separated string
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Custom Applications
    'sms_app.apps.SmsAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sms_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sms_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Manila'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Messages framework tags mapped to Bootstrap alert classes
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# ===================================================================
# IPROG SMS Provider Configuration (ACTIVE PROVIDER)
# ===================================================================
# Philippine SMS gateway: https://www.iprogsms.com
# Student accounts get 5 free SMS credits after verification.
# Create an account, verify as Student, then copy the token from API Settings.
# Leave IPROG_API_TOKEN empty to run in simulation mode.
IPROG_API_URL = os.getenv(
    'IPROG_API_URL',
    'https://www.iprogsms.com/api/v1/sms_messages'
)
IPROG_API_TOKEN = os.getenv('IPROG_API_TOKEN', '')
IPROG_STATUS_URL = os.getenv(
    'IPROG_STATUS_URL',
    'https://www.iprogsms.com/api/v1/sms_messages/status'
)

# ===================================================================
# Textbelt SMS Provider Configuration (LEGACY / FALLBACK REFERENCE)
# ===================================================================
# Philippine carriers commonly block unregistered foreign senders, so Textbelt
# is no longer the active provider. Kept here so the legacy service still runs.
TEXTBELT_API_URL = os.getenv('TEXTBELT_API_URL', 'https://textbelt.com/text')
TEXTBELT_API_KEY = os.getenv('TEXTBELT_API_KEY', 'textbelt')

# Delivery-status lookup endpoint (append /<textId>)
TEXTBELT_STATUS_URL = os.getenv('TEXTBELT_STATUS_URL', 'https://textbelt.com/status')

# Simulation toggle. When True, NO real SMS is sent and a mocked successful
# response is returned (safe for demos/tests). Set to False to send for real.
SMS_SIMULATION_MODE = os.getenv('SMS_SIMULATION_MODE', 'False').lower() in ('true', '1', 't')
