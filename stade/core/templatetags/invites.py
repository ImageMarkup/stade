from django import template

from stade.core.forms import AcceptInvitationForm
from stade.core.models import TeamInvitation

register = template.Library()


@register.inclusion_tag('pending-invites.html')
def show_pending_invites(request):
    context = {'pending_invite_forms': []}

    if request.user.is_authenticated:
        for invite in TeamInvitation.objects.filter(recipient=request.user.email):
            context['pending_invite_forms'].append(
                [invite, AcceptInvitationForm(initial={'invitation_id': invite.id})]
            )

    return context
