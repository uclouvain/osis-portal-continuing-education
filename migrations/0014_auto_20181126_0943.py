# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-26 08:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('continuing_education', '0013_admission_awareness_other'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admission',
            name='state',
            field=models.CharField(blank=True, choices=[('Accepted', 'Accepted'), ('Rejected', 'Rejected'), ('Waiting', 'Waiting'), ('Draft', 'Draft'), ('Submitted', 'Submitted')], default='Draft', max_length=50, verbose_name='State'),
        ),
    ]
