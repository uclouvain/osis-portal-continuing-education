# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-04-04 12:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('continuing_education', '0024_continuingeducationtraining_training_aid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admission',
            name='email',
            field=models.EmailField(blank=True, max_length=255, null=True, verbose_name='Additional email'),
        ),
    ]
