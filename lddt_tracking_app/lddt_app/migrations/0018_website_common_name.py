# Generated by Django 3.1.4 on 2022-09-28 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lddt_app', '0017_auto_20220512_1144'),
    ]

    operations = [
        migrations.AddField(
            model_name='website',
            name='common_name',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Common Name'),
        ),
    ]
