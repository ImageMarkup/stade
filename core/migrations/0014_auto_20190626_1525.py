# Generated by Django 2.2.2 on 2019-06-26 15:25

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


def migrate_scores(apps, schema_editor):
    Score = apps.get_model('core', 'Score')
    ScoreHistory = apps.get_model('core', 'ScoreHistory')
    for score in Score.objects.all():
        score.submission.overall_score = score.overall_score
        score.submission.score = score.score
        score.submission.fail_reason = score.fail_reason
        score.submission.save()

        ScoreHistory.objects.create(
            submission=score.submission, score=score.score, overall_score=score.overall_score
        )


class Migration(migrations.Migration):

    dependencies = [('core', '0013_auto_20190625_2007')]

    operations = [
        migrations.CreateModel(
            name='ScoreHistory',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('score', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('overall_score', models.FloatField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='submission', name='fail_reason', field=models.TextField(blank=True)
        ),
        migrations.AddField(
            model_name='submission',
            name='overall_score',
            field=models.FloatField(blank=True, default=2.2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='submission',
            name='score',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scorehistory',
            name='submission',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to='core.Submission'
            ),
        ),
        migrations.RunPython(migrate_scores),
        migrations.DeleteModel(name='Score'),
    ]