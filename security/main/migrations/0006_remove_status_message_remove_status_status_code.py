# Generated by Django 4.2.7 on 2024-03-16 22:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_status_message_status_status_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='status',
            name='message',
        ),
        migrations.RemoveField(
            model_name='status',
            name='status_code',
        ),
    ]
