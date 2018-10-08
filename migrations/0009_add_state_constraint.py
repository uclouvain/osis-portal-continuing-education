# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-05 09:19
from __future__ import unicode_literals

from django.db import migrations, models

from continuing_education.models.enums.enums import STATE_CHOICES
from continuing_education.tests.utils.utils import get_enum_keys


class Migration(migrations.Migration):

    def add_state_constraint(apps, schema_editor):
        table = apps.get_model('continuing_education', 'Admission')._meta.db_table
        schema_editor.execute(
            "ALTER TABLE %s ADD CONSTRAINT check_state CHECK (state IN %s)"
            % (table, tuple(get_enum_keys(STATE_CHOICES)))
        )

    def remove_state_constraint(apps, schema_editor):
        table = apps.get_model('continuing_education', 'Admission')._meta.db_table
        schema_editor.execute("ALTER TABLE %s DROP CONSTRAINT check_state" % table)

    dependencies = [
        ('continuing_education', '0008_auto_20181004_0023'),
    ]

    operations = [
        migrations.RunPython(add_state_constraint, reverse_code=remove_state_constraint),
        migrations.AlterField(
            model_name='admission',
            name='state',
            field=models.CharField(blank=True,
                                   choices=[('accepted', 'accepted'), ('rejected', 'rejected'), ('waiting', 'waiting')],
                                   max_length=50, null=True, verbose_name='state'),
        ),
    ]
