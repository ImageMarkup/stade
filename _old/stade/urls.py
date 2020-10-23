from django.urls import path
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view
import uritemplate  # noqa: F401

# the 'uritemplate' package is required for 'get_schema_view' to render, so ensure it's available

urlpatterns = [
    path(
        'api/docs/schema/',
        get_schema_view(
            title='ISIC Challenge',
            description='REST API for ISIC Challenge submission platform.',
            version='1.0.0',
        ),
        name='api-schema',
    ),
    path(
        'api/docs/',
        TemplateView.as_view(template_name='api.html', extra_context={'schema_url': 'api-schema'}),
        name='api-docs',
    ),
]
