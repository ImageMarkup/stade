from django.contrib import admin

from stade.core.models import TeamInvitation


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ['created', 'team_name', 'sender', 'recipient']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # TODO: Filter for permissions if non-superusers gain access to admin panel
        qs = qs.select_related('team', 'sender')
        return qs

    @admin.display(ordering='team__name')
    def team_name(self, invitation):
        return invitation.team.name
