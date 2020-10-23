from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from stade.tracker.rest import EmailCreateViewSet

router = routers.SimpleRouter(trailing_slash=False)
router.register(r'emails', EmailCreateViewSet)

urlpatterns = [path('', include(router.urls))]
