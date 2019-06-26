from django.contrib.auth.models import User
from django.core.files import File
from faker import Faker
from faker.providers import company, internet

from core.models import Task, Team, TeamInvitation, Challenge
from django.core.management.base import BaseCommand, CommandError

fake = Faker()
fake.add_provider(internet)
fake.add_provider(company)


class Command(BaseCommand):
    help = "Generate fake data for development"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        try:
            admin = User.objects.get(pk=1)
        except Exception:
            admin = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.stdout.write(self.style.SUCCESS("Created admin user: admin/password"))

        users = []
        for _ in range(3):
            users.append(
                User.objects.create(
                    username=fake.user_name(), email=fake.email(), password="letmein"
                )
            )
        challenge2017 = Challenge.objects.create(name='2017', position=1, active=True)
        challenge2018 = Challenge.objects.create(name='2018', active=True)
        with open("/code/etc/data/example_groundtruth.csv", "rb") as test_ground_truth_file:
            Task.objects.create(
                challenge=challenge2018,
                name="Diagnosis (images only)",
                description=''.join(fake.paragraphs(nb=5)),
                active=True,
                visible=True,
                test_ground_truth_file=File(test_ground_truth_file),
            )
            Task.objects.create(
                challenge=challenge2018,
                name="Diagnosis (images w/ metadata)",
                description=''.join(fake.paragraphs(nb=5)),
                active=True,
                visible=True,
                test_ground_truth_file=File(test_ground_truth_file),
            )
            Task.objects.create(
                challenge=challenge2017,
                name="Segmentation",
                description=''.join(fake.paragraphs(nb=5)),
                active=False,
                visible=True,
                test_ground_truth_file=File(test_ground_truth_file),
            )

        for challenge in challenge2017, challenge2018:
            for _ in range(2):
                team = Team.objects.create(
                    name=fake.company(),
                    institution=fake.company(),
                    challenge=challenge,
                    creator=users[0],
                )
                for u in users:
                    team.users.add(u)
                TeamInvitation.objects.create(sender=users[0], recipient=admin, team=team)
