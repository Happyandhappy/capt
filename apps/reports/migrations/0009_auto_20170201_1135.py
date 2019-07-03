# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-01 11:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_auto_20170130_1153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='cycle_period_days',
            field=models.PositiveIntegerField(choices=[(30, '30 Days'), (60, '60 Days')], default=30),
        ),
    ]
