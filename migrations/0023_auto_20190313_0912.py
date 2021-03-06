# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-03-13 08:12
from __future__ import unicode_literals

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0047_entityversion_entity_type'),
        ('continuing_education', '0022_auto_20190304_1126'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContinuingEducationTraining',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('active', models.BooleanField(default=False, verbose_name='Active')),
                ('education_group', models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, to='base.EducationGroup')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PersonTraining',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Person')),
                ('training', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='continuing_education.ContinuingEducationTraining')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='admission',
            name='formation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='continuing_education.ContinuingEducationTraining', verbose_name='Formation'),
        ),
        migrations.AddField(
            model_name='continuingeducationtraining',
            name='managers',
            field=models.ManyToManyField(through='continuing_education.PersonTraining', to='base.Person'),
        ),
    ]
