# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-16 23:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_merge_20170216_1515'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='membership',
            name='project2',
        ),
        migrations.RemoveField(
            model_name='membership',
            name='studs',
        ),
        migrations.RemoveField(
            model_name='project2',
            name='members',
        ),
        migrations.DeleteModel(
            name='Membership',
        ),
        migrations.DeleteModel(
            name='Project2',
        ),
        migrations.DeleteModel(
            name='Studs',
        ),
    ]