from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
import rules

from stade.core.models import Approach

# This file is automatically imported by rules.apps.AutodiscoverRulesConfig


@rules.predicate
def is_approach_task_locked(user: User, approach: Approach) -> bool:
    return approach.task.locked


@rules.predicate
def is_approach_team_member(user: User, approach: Approach) -> bool:
    return approach.team_id in user.teams.only('id').values_list(flat=True)


@rules.predicate
def is_approach_rate_limited(user: User, approach: Approach) -> bool:
    if approach.task.max_submissions_per_week == 0:
        return False

    submissions_in_past_week = (
        approach.task.pending_or_succeeded_submissions(approach.team)
        .filter(created__gte=timezone.now() - timedelta(weeks=1))
        .count()
    )

    return submissions_in_past_week >= approach.task.max_submissions_per_week


rules.add_perm(
    'approaches.add_submission',
    ~is_approach_task_locked & is_approach_team_member & ~is_approach_rate_limited,
)
