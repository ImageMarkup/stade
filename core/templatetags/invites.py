from django import template

from core.forms import AcceptInvitationForm

register = template.Library()


@register.inclusion_tag('pending-invites.html')
def show_pending_invites(request):
    context = {'pending_invite_forms': []}

    if request.user.is_authenticated:
        for invite in request.user.received_invites.all():
            context['pending_invite_forms'].append(
                [invite, AcceptInvitationForm(initial={"invitation_id": invite.id})]
            )

    return context
