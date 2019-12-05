from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view

urlpatterns = [
    path('', include('core.urls')),
    path('api/tracker/', include('tracker.urls')),
    path(
        'api/docs/schema/',
        # get_schema_view typing needs
        # https://github.com/typeddjango/djangorestframework-stubs/pull/44 to be released
        get_schema_view(  # type: ignore
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
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
