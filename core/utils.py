from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import is_safe_url


def safe_redirect(request, redirect_to):
    url_is_safe = is_safe_url(
        url=redirect_to, allowed_hosts=settings.ALLOWED_HOSTS, require_https=request.is_secure()
    )
    if url_is_safe and redirect_to:
        return redirect(redirect_to)
    return HttpResponseRedirect(reverse('index'))
