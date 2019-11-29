# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-09-07 08:49
from __future__ import unicode_literals

import datetime

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('base', '0040_remove_learningunitcomponent_duration'),
        ('reference', '0008_auto_20180727_1013'),
    ]

    operations = [
        migrations.CreateModel(
            name='Admission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, db_index=True, max_length=50)),
                ('last_name', models.CharField(blank=True, db_index=True, max_length=50)),
                ('birth_date', models.DateField(blank=True, default=datetime.datetime.now)),
                ('birth_location', models.CharField(blank=True, max_length=255)),
                ('gender', models.CharField(blank=True, choices=[('F', 'female'), ('M', 'male')], default='F', max_length=1)),
                ('phone_mobile', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=255)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('postal_code', models.CharField(blank=True, max_length=20)),
                ('city', models.CharField(blank=True, max_length=255)),
                ('high_school_diploma', models.BooleanField(default=False)),
                ('high_school_graduation_year', models.DateField(blank=True, default=datetime.datetime.now)),
                ('last_degree_level', models.CharField(blank=True, max_length=50)),
                ('last_degree_field', models.CharField(blank=True, max_length=50)),
                ('last_degree_institution', models.CharField(blank=True, max_length=50)),
                ('last_degree_graduation_year', models.DateField(blank=True, default=datetime.datetime.now)),
                ('other_educational_background', models.TextField(blank=True)),
                ('professional_status', models.CharField(blank=True, choices=[('EMPLOYEE', 'employee'), ('SELF_EMPLOYED', 'self_employed'), ('JOB_SEEKER', 'job_seeker'), ('PUBLIC_SERVANT', 'public_servant'), ('OTHER', 'other')], max_length=50)),
                ('current_occupation', models.CharField(blank=True, max_length=50)),
                ('current_employer', models.CharField(blank=True, max_length=50)),
                ('activity_sector', models.CharField(blank=True, choices=[('PRIVATE', 'private'), ('PUBLIC', 'public'), ('ASSOCIATIVE', 'associative'), ('HEALTH', 'health'), ('OTHER', 'other')], max_length=50)),
                ('past_professional_activities', models.TextField(blank=True)),
                ('motivation', models.TextField(blank=True)),
                ('professional_impact', models.TextField(blank=True)),
                ('courses_formula', models.CharField(blank=True, max_length=50)),
                ('program_code', models.CharField(blank=True, max_length=50)),
                ('formation_administrator', models.CharField(blank=True, max_length=50)),
                ('awareness_ucl_website', models.BooleanField(default=False)),
                ('awareness_formation_website', models.BooleanField(default=False)),
                ('awareness_press', models.BooleanField(default=False)),
                ('awareness_facebook', models.BooleanField(default=False)),
                ('awareness_linkedin', models.BooleanField(default=False)),
                ('awareness_customized_mail', models.BooleanField(default=False)),
                ('awareness_emailing', models.BooleanField(default=False)),
                ('state', models.CharField(blank=True, choices=[('accepted', 'accepted'), ('rejected', 'rejected'), ('waiting', 'waiting')], max_length=50)),
                ('registration_type', models.CharField(blank=True, choices=[('PRIVATE', 'private'), ('PROFESSIONAL', 'professional')], max_length=50)),
                ('use_address_for_billing', models.BooleanField(default=False)),
                ('billing_location', models.CharField(blank=True, max_length=255)),
                ('billing_postal_code', models.CharField(blank=True, max_length=20)),
                ('billing_city', models.CharField(blank=True, max_length=255)),
                ('head_office_name', models.CharField(blank=True, max_length=255)),
                ('company_number', models.CharField(blank=True, max_length=255)),
                ('vat_number', models.CharField(blank=True, max_length=255)),
                ('national_registry_number', models.CharField(blank=True, max_length=255)),
                ('id_card_number', models.CharField(blank=True, max_length=255)),
                ('passport_number', models.CharField(blank=True, max_length=255)),
                ('marital_status', models.CharField(blank=True, choices=[('SINGLE', 'single'), ('MARRIED', 'married'), ('WIDOWED', 'widowed'), ('DIVORCED', 'divorced'), ('SEPARATED', 'separated'), ('LEGAL_COHABITANT', 'legal_cohabitant')], max_length=255)),
                ('spouse_name', models.CharField(blank=True, max_length=255)),
                ('children_number', models.SmallIntegerField(blank=True, default=0)),
                ('previous_ucl_registration', models.BooleanField(default=False)),
                ('previous_noma', models.CharField(blank=True, max_length=255)),
                ('use_address_for_post', models.BooleanField(default=False)),
                ('residence_location', models.CharField(blank=True, max_length=255)),
                ('residence_postal_code', models.CharField(blank=True, max_length=20)),
                ('residence_city', models.CharField(blank=True, max_length=255)),
                ('residence_phone', models.CharField(blank=True, max_length=30)),
                ('registration_complete', models.BooleanField(default=False)),
                ('noma', models.CharField(blank=True, max_length=255)),
                ('payment_complete', models.BooleanField(default=False)),
                ('formation_spreading', models.BooleanField(default=False)),
                ('prior_experience_validation', models.BooleanField(default=False)),
                ('assessment_presented', models.BooleanField(default=False)),
                ('assessment_succeeded', models.BooleanField(default=False)),
                ('sessions', models.CharField(blank=True, max_length=255)),
                ('billing_country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='billing_country', to='reference.Country')),
                ('birth_country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='birth_country', to='reference.Country')),
                ('citizenship', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='citizenship', to='reference.Country')),
                ('country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='address_country', to='reference.Country')),
                ('faculty', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='base.EntityVersion')),
                ('formation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='base.OfferYear')),
                ('residence_country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='residence_country', to='reference.Country')),
            ],
        ),
    ]
