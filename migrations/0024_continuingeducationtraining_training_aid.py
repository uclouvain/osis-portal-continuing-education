# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-03-19 08:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('continuing_education', '0023_auto_20190313_0912'),
    ]

    operations = [
        migrations.AddField(
            model_name='continuingeducationtraining',
            name='training_aid',
            field=models.BooleanField(default=False, verbose_name='Training aid'),
        ),
    ]
