import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NewsSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("url", models.URLField(unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("summary", models.TextField(blank=True)),
                ("last_error", models.TextField(blank=True)),
                ("last_fetched_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="news_sources", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
    ]
