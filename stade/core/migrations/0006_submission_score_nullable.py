from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_merge_default_site'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='score',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
