# Generated by Django 5.0.2 on 2024-02-27 09:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Logs',
            new_name='Log',
        ),
    ]