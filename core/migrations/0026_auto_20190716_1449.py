# Generated by Django 2.2.2 on 2019-07-16 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('core', '0025_task_type')]

    operations = [
        migrations.AddField(
            model_name='task',
            name='max_submissions_per_week',
            field=models.PositiveSmallIntegerField(
                default=10,
                help_text='The maximum number of submissions a team can make to this task per week. Set to 0 to disable.',
                verbose_name='Maximum submissions per week',
            ),
        ),
        migrations.AlterField(
            model_name='task',
            name='max_approaches',
            field=models.PositiveSmallIntegerField(
                default=3,
                help_text='The maximum number of approaches a team can make on this task. Set to 0 to disable.',
                verbose_name='Maximum approaches',
            ),
        ),
    ]