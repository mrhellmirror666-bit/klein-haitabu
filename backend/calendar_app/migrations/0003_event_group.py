from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("calendar_app", "0002_event_visibility_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="calendarevent",
            name="group",
            field=models.CharField(
                choices=[("klein_haitabu", "Klein Haitabu"), ("dsf", "DSF")],
                default="klein_haitabu",
                max_length=30,
            ),
        ),
    ]
