from typing import List, Type

from rest_framework import viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.mixins import CreateModelMixin

from tracker.models import Email
from tracker.serializers import EmailSerializer


class EmailCreateViewSet(CreateModelMixin, viewsets.GenericViewSet):
    # no auth required for tracking emails
    authentication_classes: List[Type[BaseAuthentication]] = []

    queryset = Email.objects.all()
    serializer_class = EmailSerializer
