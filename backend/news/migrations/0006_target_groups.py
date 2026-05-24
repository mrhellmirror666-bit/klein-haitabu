from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0005_source_discovery_display_option"),
    ]

    operations = [
        migrations.AddField(
            model_name="newssource",
            name="target_group",
            field=models.CharField(
                choices=[("all", "Alle Gruppen"), ("klein_haitabu", "Klein Haitabu"), ("dsf", "DSF")],
                default="all",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="sourcediscovery",
            name="target_group",
            field=models.CharField(
                choices=[("all", "Alle Gruppen"), ("klein_haitabu", "Klein Haitabu"), ("dsf", "DSF")],
                default="all",
                max_length=30,
            ),
        ),
    ]
