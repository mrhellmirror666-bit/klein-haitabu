from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("calendar_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="calendarevent",
            name="visibility",
            field=models.CharField(
                choices=[("users", "Nutzer"), ("guests", "Gaeste"), ("public", "Oeffentlich")],
                default="users",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="calendarevent",
            name="tags",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
