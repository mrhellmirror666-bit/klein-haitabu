from django.db import migrations


GROUPS = (
    ("klein_haitabu", "Klein Haitabu"),
    ("dsf", "DSF"),
)


def create_groups(apps, schema_editor):
    Group = apps.get_model("common", "Group")
    for slug, name in GROUPS:
        Group.objects.get_or_create(slug=slug, defaults={"name": name})


def remove_groups(apps, schema_editor):
    Group = apps.get_model("common", "Group")
    Group.objects.filter(slug__in=[slug for slug, _name in GROUPS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_groups, reverse_code=remove_groups),
    ]
