# Generated by Django 2.2.2 on 2019-06-20 18:22
import django.core.validators
from django.db import migrations, models

import core.models


class Migration(migrations.Migration):

    dependencies = [('core', '0002_auto_20190619_1753')]

    operations = [
        migrations.AlterField(
            model_name='approach',
            name='manuscript',
            field=models.FileField(
                max_length=200,
                upload_to=core.models.submission_file_upload_to,
                validators=[
                    django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])
                ],
            ),
        )
    ]
