from django.utils.encoding import force_str
from rest_framework import serializers, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.fields import EmailField
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny

from stade.tracker.models import Email


class ConflictException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A server error occurred.'

    def __init__(self, detail, field, code):
        if code is not None:
            self.status_code = code
        if detail is not None:
            self.detail = {field: force_str(detail)}
        else:
            self.detail = {'detail': force_str(self.default_detail)}


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = '__all__'

    email = EmailField()

    def validate_email(self, value):
        if Email.objects.filter(email=value).exists():
            raise ConflictException('Email already exists', 'email', status.HTTP_409_CONFLICT)
        return value


class EmailCreateViewSet(CreateModelMixin, viewsets.GenericViewSet):
    # no auth required for tracking emails
    permission_classes = [AllowAny]

    queryset = Email.objects.all()
    serializer_class = EmailSerializer
