# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-24 09:19
from __future__ import unicode_literals

import datetime

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('continuing_education', '0004_merge_20180924_1053'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='address',
        ),
        migrations.RemoveField(
            model_name='person',
            name='birth_country',
        ),
        migrations.RemoveField(
            model_name='person',
            name='citizenship',
        ),
        migrations.RemoveField(
            model_name='admission',
            name='person',
        ),
        migrations.RemoveField(
            model_name='continuingeducationperson',
            name='city',
        ),
        migrations.RemoveField(
            model_name='continuingeducationperson',
            name='country',
        ),
        migrations.RemoveField(
            model_name='continuingeducationperson',
            name='location',
        ),
        migrations.RemoveField(
            model_name='continuingeducationperson',
            name='postal_code',
        ),
        migrations.AddField(
            model_name='admission',
            name='person_information',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='continuing_education.ContinuingEducationPerson'),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='activity_sector',
            field=models.CharField(blank=True, choices=[('PRIVATE', 'private'), ('PUBLIC', 'public'), ('ASSOCIATIVE', 'associative'), ('HEALTH', 'health'), ('OTHER', 'other')], max_length=50),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='continuing_education.Address'),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='current_employer',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='current_occupation',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='email',
            field=models.EmailField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='high_school_diploma',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='high_school_graduation_year',
            field=models.DateField(blank=True, default=datetime.datetime.now),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='last_degree_field',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='last_degree_graduation_year',
            field=models.DateField(blank=True, default=datetime.datetime.now),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='last_degree_institution',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='last_degree_level',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='other_educational_background',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='past_professional_activities',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='phone_mobile',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='continuingeducationperson',
            name='professional_status',
            field=models.CharField(blank=True, choices=[('EMPLOYEE', 'employee'), ('SELF_EMPLOYED', 'self_employed'), ('JOB_SEEKER', 'job_seeker'), ('PUBLIC_SERVANT', 'public_servant'), ('OTHER', 'other')], max_length=50),
        ),
        migrations.DeleteModel(
            name='Person',
        ),
    ]
