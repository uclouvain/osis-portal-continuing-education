# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-14 19:39
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reference', '0008_auto_20180727_1013'),
        ('base', '0040_remove_learningunitcomponent_duration'),
        ('continuing_education', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContinuingEducationPerson',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('birth_location', models.CharField(blank=True, max_length=255)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('postal_code', models.CharField(blank=True, max_length=20)),
                ('city', models.CharField(blank=True, max_length=255)),
                ('birth_country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='birth_country', to='reference.Country')),
                ('citizenship', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='citizenship', to='reference.Country')),
                ('country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='address_country', to='reference.Country')),
                ('person', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='base.Person')),
            ],
        ),
    ]
