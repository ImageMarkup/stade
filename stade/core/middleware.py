from django.utils import timezone
import pytz


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_staff:
            timezone.activate(pytz.timezone('America/New_York'))
        else:
            timezone.deactivate()
        return self.get_response(request)
