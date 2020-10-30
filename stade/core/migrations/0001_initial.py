# Generated by Django 3.0.3 on 2020-02-07 02:30

from django.conf import settings
import django.contrib.postgres.fields.jsonb
import django.core.validators
from django.db import migrations, models
import django.utils.timezone
import s3_file_field.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Approach',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('docker_tag', models.CharField(blank=True, max_length=120)),
                (
                    'uses_external_data',
                    models.BooleanField(choices=[(True, 'Yes'), (False, 'No')], default=False),
                ),
                (
                    'manuscript',
                    s3_file_field.fields.S3FileField(
                        blank=True,
                        max_length=2000,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                allowed_extensions=['pdf']
                            )
                        ],
                    ),
                ),
                (
                    'review_state',
                    models.CharField(
                        blank=True,
                        choices=[('accepted', 'Accepted'), ('rejected', 'Rejected')],
                        default='',
                        max_length=8,
                    ),
                ),
                (
                    'reject_reason',
                    models.CharField(
                        blank=True,
                        choices=[
                            ('blank_or_corrupt_manuscript', 'Blank or corrupt manuscript'),
                            ('low_quality_manuscript', 'Low quality manuscript'),
                            ('rule_violation', 'Violation of rules'),
                        ],
                        default='',
                        max_length=27,
                    ),
                ),
                (
                    'review_assignee',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={'verbose_name_plural': 'approaches'},
        ),
        migrations.CreateModel(
            name='Challenge',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=100, unique=True)),
                (
                    'locked',
                    models.BooleanField(
                        default=True,
                        help_text='Whether users are blocked from making and editing teams.',
                    ),
                ),
                ('position', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'ordering': ['position']},
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('accepted_terms', models.BooleanField(default=False)),
                (
                    'test_prediction_file',
                    s3_file_field.fields.S3FileField(
                        max_length=2000,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('queued', 'Queued for scoring'),
                            ('scoring', 'Scoring'),
                            ('internal_failure', 'Internal failure'),
                            ('failed', 'Failed'),
                            ('succeeded', 'Succeeded'),
                        ],
                        default='queued',
                        max_length=20,
                    ),
                ),
                ('score', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('overall_score', models.FloatField(blank=True, null=True)),
                ('validation_score', models.FloatField(blank=True, null=True)),
                ('fail_reason', models.TextField(blank=True)),
                (
                    'approach',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='core.Approach'
                    ),
                ),
                (
                    'creator',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={'ordering': ['-created']},
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=100)),
                ('institution', models.CharField(blank=True, max_length=100)),
                ('institution_url', models.URLField(blank=True)),
                (
                    'challenge',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='core.Challenge'
                    ),
                ),
                (
                    'creator',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    'users',
                    models.ManyToManyField(related_name='teams', to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={'unique_together': {('challenge', 'name')}},
        ),
        migrations.CreateModel(
            name='TeamInvitation',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('recipient', models.EmailField(db_index=True, max_length=254)),
                (
                    'sender',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='sent_invites',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'team',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Team'),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'type',
                    models.CharField(
                        choices=[
                            ('segmentation', 'Segmentation'),
                            ('classification', 'Classification'),
                        ],
                        max_length=20,
                    ),
                ),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('short_description', models.TextField()),
                (
                    'locked',
                    models.BooleanField(
                        default=True,
                        help_text='Whether users are blocked from making and editing approaches '
                        'and submissions.',
                    ),
                ),
                (
                    'hidden',
                    models.BooleanField(
                        default=True, help_text='Whether the task is invisible to users.'
                    ),
                ),
                (
                    'scores_published',
                    models.BooleanField(
                        default=False,
                        help_text='Whether final scores are visible to submitters and the '
                        'leaderboard is open.',
                    ),
                ),
                (
                    'max_approaches',
                    models.PositiveSmallIntegerField(
                        default=3,
                        help_text='The maximum number of approaches a team can make on this task. '
                        'Set to 0 to disable.',
                        verbose_name='Maximum approaches',
                    ),
                ),
                (
                    'max_submissions_per_week',
                    models.PositiveSmallIntegerField(
                        default=10,
                        help_text='The maximum number of submissions a team can make to this '
                        'task per week. Set to 0 to disable.',
                        verbose_name='Maximum submissions per week',
                    ),
                ),
                (
                    'requires_manuscript',
                    models.BooleanField(
                        default=True,
                        help_text='Whether approaches should require a manuscript.',
                        verbose_name='Requires a manuscript',
                    ),
                ),
                (
                    'test_ground_truth_file',
                    s3_file_field.fields.S3FileField(
                        max_length=2000,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                    ),
                ),
                (
                    'challenge',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='tasks',
                        to='core.Challenge',
                    ),
                ),
            ],
            options={'ordering': ['id']},
        ),
        migrations.CreateModel(
            name='ReviewHistory',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                (
                    'review_state',
                    models.CharField(
                        choices=[('accepted', 'Accepted'), ('rejected', 'Rejected')], max_length=8
                    ),
                ),
                (
                    'reject_reason',
                    models.CharField(
                        blank=True,
                        choices=[
                            ('blank_or_corrupt_manuscript', 'Blank or corrupt manuscript'),
                            ('low_quality_manuscript', 'Low quality manuscript'),
                            ('rule_violation', 'Violation of rules'),
                        ],
                        default='',
                        max_length=27,
                    ),
                ),
                (
                    'approach',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='review_history',
                        to='core.Approach',
                    ),
                ),
                (
                    'reviewed_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={'ordering': ['-created']},
        ),
        migrations.AddField(
            model_name='approach',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Task'),
        ),
        migrations.AddField(
            model_name='approach',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Team'),
        ),
        migrations.AddConstraint(
            model_name='approach',
            constraint=models.UniqueConstraint(
                fields=('name', 'task', 'team'), name='unique_approaches'
            ),
        ),
    ]