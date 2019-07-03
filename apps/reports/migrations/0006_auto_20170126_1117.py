# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-26 11:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_auto_20170123_1517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='cycle_period_days',
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='is_managed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='target_cpa',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
