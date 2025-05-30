# Generated by Django 5.1.3 on 2025-05-24 03:09

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedifyApp', '0006_fileasset_imageasset_delete_digitalassets_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeatherStatusImages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(max_length=500)),
                ('status', models.CharField(choices=[('SUNNY', 'Sunny'), ('CLOUDY', 'Cloudy'), ('RAINY', 'Rainy'), ('STORMY', 'Stormy'), ('SNOWY', 'Snowy'), ('FOGGY', 'Foggy'), ('DRIZZLY', 'Drizzly'), ('THUNDERY', 'Thundery')], max_length=20)),
            ],
        ),
        migrations.AlterField(
            model_name='authtoken',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 24, 15, 9, 58, 977400, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='scheduleitemlist',
            name='lastScheduleOn',
            field=models.CharField(default='24-05-2025 08:39:58 AM', max_length=200),
        ),
    ]
