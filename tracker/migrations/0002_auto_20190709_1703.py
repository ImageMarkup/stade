# Generated by Django 2.2.2 on 2019-07-09 17:03

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
