# Generated by Django 5.0.2 on 2024-03-07 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitor", "0024_remove_emailvalues_monitor_id_emailvalues_monitor"),
    ]

    operations = [
        migrations.AlterField(
            model_name="monitor",
            name="days_before_exp",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Ile dni przed poinformować?"
            ),
        ),
    ]