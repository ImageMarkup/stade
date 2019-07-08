from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=False)
router.register(r'emails', views.EmailCreateViewSet)
urlpatterns = [path('', include(router.urls))]
