import math
from typing import Any, Dict

from dictdiffer import diff
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import is_safe_url

from core.models import Submission


def safe_redirect(request, redirect_to):
    url_is_safe = is_safe_url(
        url=redirect_to, allowed_hosts=settings.ALLOWED_HOSTS, require_https=request.is_secure()
    )
    if url_is_safe and redirect_to:
        return redirect(redirect_to)
    return HttpResponseRedirect(reverse('index'))


def changes(s1: Submission, s2: Submission) -> Dict[str, Any]:
    c: Dict[str, Any] = {}

    if s1.status != s2.status:
        c['status'] = [s1.status, s2.status]

    if s1.overall_score != s2.overall_score:
        if (s1.overall_score is None or s2.overall_score is None) or (
            not math.isclose(s1.overall_score, s2.overall_score)
        ):
            c['overall score'] = [s1.overall_score, s2.overall_score]

    if s1.validation_score != s2.validation_score:
        if (s1.validation_score is None or s2.validation_score is None) or (
            not math.isclose(s1.validation_score, s2.validation_score)
        ):
            c['validation score'] = [s1.validation_score, s2.validation_score]

    for d in diff(s1.score, s2.score):
        if d[0] == 'change':
            key = d[1] if d[1] != '' else 'score'

            if key in ['roc', 'score']:
                c[key] = ['', 'changed']
            else:
                c[key] = d[2]
        elif d[0] == 'add':
            c[d[1]] = ['', 'added']
        elif d[0] == 'remove':
            c[d[1]] = ['', 'removed']
        else:
            raise Exception(d)

    return c
