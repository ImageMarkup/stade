# Generated by Django 3.1.4 on 2020-12-10 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_merge_20201203_2200'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='creator_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]