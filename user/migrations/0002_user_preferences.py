from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="preferred_currency",
            field=models.CharField(default="GBP", max_length=3),
        ),
        migrations.AddField(
            model_name="user",
            name="preferred_timezone",
            field=models.CharField(default="UTC", max_length=64),
        ),
    ]

