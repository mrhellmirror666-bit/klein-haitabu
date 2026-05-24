import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0003_source_search_options_and_discoveries"),
    ]

    operations = [
        migrations.AddField(
            model_name="sourcediscovery",
            name="import_error",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="sourcediscovery",
            name="imported_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sourcediscovery",
            name="is_imported",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="ImportedExternalItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_type", models.CharField(choices=[("calendar", "Kalender"), ("table", "Tabelle")], max_length=20)),
                ("title", models.CharField(max_length=220)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("content", models.TextField(blank=True)),
                ("source_url", models.URLField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("discovery", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="imported_items", to="news.sourcediscovery")),
            ],
            options={
                "ordering": ["item_type", "starts_at", "title"],
            },
        ),
    ]
