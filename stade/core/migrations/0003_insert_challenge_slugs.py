# Generated by Django 3.0.3 on 2020-02-28 15:16

from django.db import migrations


def generate_challenge_slugs(apps, schema_editor):
    Challenge = apps.get_model('core', 'Challenge')  # noqa: N806

    challenge_slugs = {37: 'sandbox', 36: '2018', 35: '2017', 34: '2016', 38: 'live', 39: '2019'}

    for id_, slug in challenge_slugs.items():
        try:
            challenge = Challenge.objects.get(pk=id_)
            challenge.slug = slug
            challenge.save(update_fields=['slug'])
        except Challenge.DoesNotExist:  # these don't exist in testing
            pass


class Migration(migrations.Migration):
    dependencies = [('core', '0002_add_challenge_slug')]
    operations = [migrations.RunPython(generate_challenge_slugs)]
