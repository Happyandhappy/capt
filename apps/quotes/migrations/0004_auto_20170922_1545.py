# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-22 14:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0003_auto_20170922_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quote',
            name='quote',
            field=models.BigIntegerField(verbose_name='Quote'),
        ),
    ]
