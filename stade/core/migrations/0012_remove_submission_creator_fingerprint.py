# Generated by Django 3.2 on 2021-04-07 02:41

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0011_auto_20210129_1835'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='creator_fingerprint',
        ),
    ]
