# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-01 08:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('continuing_education', '0006_auto_20180930_1248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admission',
            name='formation',
            field=models.CharField(max_length=50, verbose_name='formation'),
        ),
    ]
