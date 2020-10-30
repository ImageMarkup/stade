# Generated by Django 2.2.1 on 2019-05-13 10:27
from typing import List, Tuple

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies: List[Tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
            ],
        )
    ]