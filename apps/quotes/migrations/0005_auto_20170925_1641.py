# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-25 15:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0004_auto_20170922_1545'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quote',
            name='monthly_adwords_spend',
            field=models.DecimalField(decimal_places=2, max_digits=30, verbose_name='Monthly Google Adwords Spend'),
        ),
    ]