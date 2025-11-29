# alx_travel_app/settings.py
INSTALLED_APPS = [
    # ... other apps
    'rest_framework',
    'drf_yasg',
    'listings',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}