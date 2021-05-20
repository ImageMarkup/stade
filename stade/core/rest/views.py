import logging

from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from stade.core.leaderboard import submissions_by_approach, submissions_by_team
from stade.core.models import Challenge, Submission, Task
from stade.core.rest.serializers import ChallengeSerializer, LeaderboardEntrySerializer

logger = logging.getLogger(__name__)


@api_view(['GET'])
def challenge_detail(request, challenge_id):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    serializer = ChallengeSerializer(challenge)
    return Response(serializer.data)


@api_view(['GET'])
def leaderboard(request, task_id, cluster):
    if request.user.is_staff:
        task = get_object_or_404(Task, pk=task_id)
    else:
        task = get_object_or_404(Task.objects.filter(scores_published=True), pk=task_id)

    paginator = LimitOffsetPagination()
    paginator.default_limit = paginator.max_limit = 200

    if cluster == 'approach':
        submission_ids = submissions_by_approach(task.id)
    elif cluster == 'team':
        submission_ids = submissions_by_team(task.id)
    else:
        raise Http404()

    leaderboard_submissions = (
        Submission.objects.select_related('approach', 'approach__team')
        .filter(id__in=submission_ids)
        .order_by('-overall_score', 'created')
    )

    result_page = paginator.paginate_queryset(leaderboard_submissions, request)
    serializer = LeaderboardEntrySerializer(result_page, many=True, context={'request': request})

    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def submission_scores(request, submission_id):
    if request.user.is_staff:
        # Remove all deferred fields, since we want the score immediately
        submission = get_object_or_404(Submission.objects.defer(None), pk=submission_id)
    else:
        # Remove all deferred fields, since we want the score immediately
        submission = get_object_or_404(
            Submission.objects.defer(None).filter(approach__task__scores_published=True),
            pk=submission_id,
        )

    if isinstance(submission.score, list):
        logger.warning('Unable to serialize submission score')
        return JsonResponse({})

    return JsonResponse(submission.score)
