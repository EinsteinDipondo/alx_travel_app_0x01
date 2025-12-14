import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Chapa Configuration
CHAPA_SECRET_KEY = os.getenv('CHAPA_SECRET_KEY')
CHAPA_API_URL = os.getenv('CHAPA_API_URL')
CHAPA_VERIFY_URL = os.getenv('CHAPA_VERIFY_URL')
CHAPA_WEBHOOK_URL = os.getenv('CHAPA_WEBHOOK_URL')

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER')

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps ...
    'rest_framework',
    'django_celery_results',
    'listings',
]

# Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}