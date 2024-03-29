# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-09 08:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    def remove_state_constraint(apps, schema_editor):
        table = apps.get_model('continuing_education', 'Admission')._meta.db_table
        schema_editor.execute("ALTER TABLE %s DROP CONSTRAINT check_state" % table)

    dependencies = [
        ('continuing_education', '0009_add_state_constraint'),
    ]

    operations = [
        migrations.RunPython(remove_state_constraint, migrations.RunPython.noop),
    ]
