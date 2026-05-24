import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="NewsItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220)),
                ("url", models.URLField()),
                ("summary", models.TextField()),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="news.newssource")),
            ],
            options={
                "ordering": ["-published_at", "-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="newsitem",
            constraint=models.UniqueConstraint(fields=("source", "url"), name="unique_news_item_per_source_url"),
        ),
    ]
