# Generated by Django 4.0.3 on 2022-03-17 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_remove_submission_creator_fingerprint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='approach',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='reviewhistory',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='submission',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='task',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='team',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='teaminvitation',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
    ]
