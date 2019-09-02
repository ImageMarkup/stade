from rest_framework import serializers


class LeaderboardEntrySerializer(serializers.Serializer):
    submission_id = serializers.IntegerField(source='id')
    approach_name = serializers.CharField(source='approach.name')
    approach_manuscript_url = serializers.SerializerMethodField()
    approach_uses_external_data = serializers.BooleanField(source='approach.uses_external_data')
    overall_score = serializers.FloatField()
    submission_created = serializers.DateTimeField(source='created')
    team_name = serializers.CharField(source='approach.team.name')
    team_institution_name = serializers.SerializerMethodField()
    team_institution_url = serializers.SerializerMethodField()

    def get_team_institution_url(self, submission):
        return (
            None
            if not submission.approach.team.institution_url
            else submission.approach.team.institution_url
        )

    def get_team_institution_name(self, submission):
        return (
            None
            if not submission.approach.team.institution
            else submission.approach.team.institution
        )

    def get_approach_manuscript_url(self, submission):
        if submission.approach.manuscript:
            return self.context['request'].build_absolute_uri(submission.approach.manuscript.url)
        else:
            # historical reasons, as well as the live challenge not requiring manuscripts
            return None
