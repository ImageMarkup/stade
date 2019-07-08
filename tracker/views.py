from rest_framework import viewsets
from rest_framework.mixins import CreateModelMixin

from tracker.models import Email
from tracker.serializers import EmailSerializer


class EmailCreateViewSet(CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = []  # no auth required for tracking emails
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
