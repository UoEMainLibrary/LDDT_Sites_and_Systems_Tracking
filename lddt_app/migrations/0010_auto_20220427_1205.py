# Generated by Django 3.1.4 on 2022-04-27 12:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lddt_app', '0009_auto_20220427_1100'),
    ]

    operations = [
        migrations.RenameField(
            model_name='website',
            old_name='dns_ip_address',
            new_name='vm_ip_address',
        ),
    ]
