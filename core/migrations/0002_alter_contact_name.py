# Generated by Django 5.1.3 on 2024-12-09 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='name',
            field=models.CharField(max_length=1000, verbose_name='ФИО'),
        ),
    ]
