# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-23 15:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_auto_20170123_1501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='max_cpc_limit',
            field=models.DecimalField(decimal_places=2, default=1000, max_digits=10),
        ),
    ]
