# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-30 11:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0007_auto_20170130_1123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='keywordevent',
            name='new_max_cpc',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='keywordevent',
            name='previous_max_cpc',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]