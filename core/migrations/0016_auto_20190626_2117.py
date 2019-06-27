# Generated by Django 2.2.2 on 2019-06-26 21:17

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [('core', '0015_auto_20190626_2109')]

    operations = [
        migrations.AlterField(
            model_name='scorehistory', name='overall_score', field=models.FloatField()
        ),
        migrations.AlterField(
            model_name='scorehistory',
            name='score',
            field=django.contrib.postgres.fields.jsonb.JSONField(),
        ),
        migrations.AlterField(
            model_name='scorehistory',
            name='submission',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='score_history',
                to='core.Submission',
            ),
        ),
    ]