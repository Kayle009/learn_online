# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-01 05:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20170801_0520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='image',
            field=models.ImageField(blank=True, default='image/default.png', upload_to='image/%Y/%m', verbose_name='头像'),
        ),
    ]
