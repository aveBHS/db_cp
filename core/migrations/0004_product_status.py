# Generated by Django 5.1.3 on 2024-12-11 08:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_productstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='core.productstatus', verbose_name='Статус'),
            preserve_default=False,
        ),
    ]