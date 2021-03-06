# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-13 16:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0013_campaign_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='cycle_period_days',
            field=models.PositiveIntegerField(choices=[(30, '30 days'), (60, '60 days'), (180, '180 days'), (365, '365 days')], default=30, help_text='The time period with the most relevant data', verbose_name='Cycle Period'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='max_cpc_limit',
            field=models.PositiveIntegerField(default=10000000, help_text='The maximum you would like to pay per click', verbose_name='Cost per Click (CPC) limit in £'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='target_cpa',
            field=models.PositiveIntegerField(default=0, help_text='The average amount you would like to pay for a conversion', verbose_name='Target Cost per Acquisition (CPA) in £'),
        ),
    ]
