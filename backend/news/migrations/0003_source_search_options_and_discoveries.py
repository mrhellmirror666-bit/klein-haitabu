import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0002_newsitem"),
    ]

    operations = [
        migrations.AddField(
            model_name="newssource",
            name="search_calendars",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="newssource",
            name="search_news",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="newssource",
            name="search_tables",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="SourceDiscovery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("discovery_type", models.CharField(choices=[("calendar", "Kalender"), ("table", "Tabelle")], max_length=20)),
                ("title", models.CharField(max_length=220)),
                ("url", models.URLField()),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="discoveries", to="news.newssource")),
            ],
            options={
                "ordering": ["discovery_type", "title"],
            },
        ),
        migrations.AddConstraint(
            model_name="sourcediscovery",
            constraint=models.UniqueConstraint(fields=("source", "discovery_type", "url"), name="unique_source_discovery"),
        ),
    ]
