from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0004_imported_external_items"),
    ]

    operations = [
        migrations.AddField(
            model_name="sourcediscovery",
            name="show_on_main_page",
            field=models.BooleanField(default=True),
        ),
    ]
