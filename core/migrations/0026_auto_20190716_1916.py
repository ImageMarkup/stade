# Generated by Django 2.2.2 on 2019-07-16 19:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('core', '0025_task_type')]

    operations = [
        migrations.AlterModelOptions(name='challenge', options={'ordering': ['position']}),
        migrations.AlterModelOptions(name='scorehistory', options={'ordering': ['-created']}),
        migrations.AlterModelOptions(name='submission', options={'ordering': ['-created']}),
    ]