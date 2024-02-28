# Generated by Django 4.2.10 on 2024-02-28 14:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0009_alter_email_options_remove_email_monitor_id_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='emailvalues',
            options={'ordering': ['email'], 'verbose_name': 'Emaile'},
        ),
        migrations.AlterField(
            model_name='emailvalues',
            name='email',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='monitor.email', verbose_name='Adres e-mail'),
        ),
    ]