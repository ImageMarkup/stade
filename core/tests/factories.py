from django.contrib.auth.models import User
import factory


class ChallengeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'core.challenge'

    name = factory.Faker('sentence', nb_words=2)


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'core.task'

    name = factory.Faker('sentence', nb_words=2)
    challenge = factory.SubFactory(ChallengeFactory)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'user_%d' % n)
    email = factory.Sequence(lambda n: 'user_%d' % n)


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'core.team'

    name = factory.Sequence(lambda n: 'team_%d' % n)
    creator = factory.SubFactory(UserFactory)
    challenge = factory.SubFactory(ChallengeFactory)


class ApproachFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'core.approach'

    name = factory.Sequence(lambda n: 'approach_%d' % n)
    uses_external_data = factory.Faker('boolean')
    manuscript = factory.django.FileField(filename='test-manuscript.pdf')
    task = factory.SubFactory(TaskFactory)
    team = factory.SubFactory(TeamFactory)


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'core.submission'

    creator = factory.SubFactory(UserFactory)
    approach = factory.SubFactory(ApproachFactory)
