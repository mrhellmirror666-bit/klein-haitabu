import common.models
import django.db.models.deletion
from django.db import migrations, models


def copy_group_to_fk(apps, schema_editor):
    CalendarEvent = apps.get_model("calendar_app", "CalendarEvent")
    Group = apps.get_model("common", "Group")
    default_group = Group.objects.get(slug="klein_haitabu")

    for event in CalendarEvent.objects.all():
        group = Group.objects.filter(slug=event.group_slug).first() or default_group
        event.group_id = group.pk
        event.save(update_fields=["group"])


def copy_group_to_slug(apps, schema_editor):
    CalendarEvent = apps.get_model("calendar_app", "CalendarEvent")
    Group = apps.get_model("common", "Group")

    for event in CalendarEvent.objects.all():
        group = Group.objects.filter(pk=event.group_id).first()
        event.group_slug = group.slug if group else "klein_haitabu"
        event.save(update_fields=["group_slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0002_seed_groups"),
        ("calendar_app", "0003_event_group"),
    ]

    operations = [
        migrations.RenameField(
            model_name="calendarevent",
            old_name="group",
            new_name="group_slug",
        ),
        migrations.AddField(
            model_name="calendarevent",
            name="group",
            field=models.ForeignKey(
                default=common.models.get_default_group_id,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="calendar_events",
                to="common.group",
            ),
        ),
        migrations.RunPython(copy_group_to_fk, reverse_code=copy_group_to_slug),
        migrations.AlterField(
            model_name="calendarevent",
            name="group",
            field=models.ForeignKey(
                default=common.models.get_default_group_id,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="calendar_events",
                to="common.group",
            ),
        ),
        migrations.RemoveField(
            model_name="calendarevent",
            name="group_slug",
        ),
    ]
