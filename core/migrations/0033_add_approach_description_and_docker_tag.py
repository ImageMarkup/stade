# Generated by Django 2.2.2 on 2019-08-01 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('core', '0032_add_invite_recipient_index')]

    operations = [
        migrations.AddField(
            model_name='approach', name='description', field=models.TextField(blank=True)
        ),
        migrations.AddField(
            model_name='approach',
            name='docker_tag',
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
