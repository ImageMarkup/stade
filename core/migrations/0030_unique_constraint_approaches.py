# Generated by Django 2.2.2 on 2019-07-22 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('core', '0029_merge_duplicate_approaches')]

    operations = [
        migrations.AddConstraint(
            model_name='approach',
            constraint=models.UniqueConstraint(
                fields=('name', 'task', 'team'), name='unique_approaches'
            ),
        )
    ]