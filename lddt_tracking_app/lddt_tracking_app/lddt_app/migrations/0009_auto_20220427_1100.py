# Generated by Django 3.1.4 on 2022-04-27 11:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lddt_app', '0008_auto_20220426_1046'),
    ]

    operations = [
        migrations.RenameField(
            model_name='website',
            old_name='ip_address',
            new_name='dns_ip_address',
        ),
    ]
