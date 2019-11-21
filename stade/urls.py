from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path('', include('core.urls')),
    path('api/tracker/', include('tracker.urls')),
    path('api/docs/', include_docs_urls()),
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += path('api/joist', include('joist.urls'))