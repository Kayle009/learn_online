# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-01 05:20
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='birthday',
            field=models.DateField(blank=True, default=datetime.datetime.now, verbose_name='生日'),
        ),
    ]
