import pathlib

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from faker import Faker
from faker.providers import company, internet

from stade.core.models import Challenge, Task, Team, TeamInvitation

fake = Faker()
fake.add_provider(internet)
fake.add_provider(company)


class Command(BaseCommand):
    help = 'Generate fake data for development'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        try:
            admin = User.objects.get(pk=1)
        except Exception:
            admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.stdout.write(self.style.SUCCESS('Created admin user: admin/password'))

        users = []
        for _ in range(3):
            users.append(
                User.objects.create(
                    username=fake.user_name(), email=fake.email(), password='letmein'
                )
            )
        localdev = Challenge.objects.create(name='local dev', position=1, locked=False)
        with (pathlib.Path(__file__).parent / 'data' / 'example_groundtruth.csv').open(
            'rb'
        ) as test_ground_truth_file:
            Task.objects.create(
                challenge=localdev,
                name='Local development',
                description=''.join(fake.paragraphs(nb=5)),
                short_description=''.join(fake.paragraphs(nb=1)),
                locked=False,
                hidden=False,
                test_ground_truth_file=File(test_ground_truth_file),
            )
        for _ in range(2):
            team = Team.objects.create(
                name=fake.company(),
                institution=fake.company(),
                challenge=localdev,
                creator=users[0],
            )
            for u in users:
                team.users.add(u)
            TeamInvitation.objects.create(sender=users[0], recipient=admin.email, team=team)
