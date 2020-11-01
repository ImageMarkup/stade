from django.contrib.auth.models import User
import factory.django

from stade.core.models import Approach, Challenge, Submission, Task, Team


class ChallengeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Challenge

    name = factory.Faker('sentence', nb_words=2)


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    type = Task.Type.CLASSIFICATION
    name = factory.Faker('sentence', nb_words=2)
    challenge = factory.SubFactory(ChallengeFactory)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.SelfAttribute('email')
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Sequence(lambda n: 'team_%d' % n)
    creator = factory.SubFactory(UserFactory)
    challenge = factory.SubFactory(ChallengeFactory)


class ApproachFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Approach

    name = factory.Sequence(lambda n: 'approach_%d' % n)
    uses_external_data = factory.Faker('boolean')
    manuscript = factory.django.FileField(filename='test-manuscript.pdf')
    task = factory.SubFactory(TaskFactory)
    team = factory.SubFactory(TeamFactory)


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submission

    creator = factory.SubFactory(UserFactory)
    approach = factory.SubFactory(ApproachFactory)
