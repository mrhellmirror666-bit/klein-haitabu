import django.db.models.deletion
from django.db import migrations, models


def copy_group_to_fk(apps, schema_editor):
    Group = apps.get_model("common", "Group")
    NewsSource = apps.get_model("news", "NewsSource")
    SourceDiscovery = apps.get_model("news", "SourceDiscovery")

    for model in (NewsSource, SourceDiscovery):
        for obj in model.objects.all():
            if obj.target_group_slug == "all":
                obj.target_group = None
            else:
                obj.target_group = Group.objects.filter(slug=obj.target_group_slug).first()
            obj.save(update_fields=["target_group"])


def copy_group_to_slug(apps, schema_editor):
    Group = apps.get_model("common", "Group")
    NewsSource = apps.get_model("news", "NewsSource")
    SourceDiscovery = apps.get_model("news", "SourceDiscovery")

    for model in (NewsSource, SourceDiscovery):
        for obj in model.objects.all():
            group = Group.objects.filter(pk=obj.target_group_id).first()
            obj.target_group_slug = group.slug if group else "all"
            obj.save(update_fields=["target_group_slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0002_seed_groups"),
        ("news", "0006_target_groups"),
    ]

    operations = [
        migrations.RenameField(
            model_name="newssource",
            old_name="target_group",
            new_name="target_group_slug",
        ),
        migrations.RenameField(
            model_name="sourcediscovery",
            old_name="target_group",
            new_name="target_group_slug",
        ),
        migrations.AddField(
            model_name="newssource",
            name="target_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="news_sources",
                to="common.group",
            ),
        ),
        migrations.AddField(
            model_name="sourcediscovery",
            name="target_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="source_discoveries",
                to="common.group",
            ),
        ),
        migrations.RunPython(copy_group_to_fk, reverse_code=copy_group_to_slug),
        migrations.RemoveField(
            model_name="newssource",
            name="target_group_slug",
        ),
        migrations.RemoveField(
            model_name="sourcediscovery",
            name="target_group_slug",
        ),
    ]
