from django.db import migrations


def normalize_roles(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    User.objects.filter(is_superuser=True).update(role="admin", is_staff=True)
    User.objects.filter(role="guest", is_superuser=False).update(is_staff=False)


def reverse_normalize_roles(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(normalize_roles, reverse_normalize_roles),
    ]
