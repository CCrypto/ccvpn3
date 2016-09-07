# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-07 00:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_auto_20160904_0048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.CharField(choices=[('new', 'Created'), ('unconfirmed', 'Waiting for payment'), ('active', 'Active'), ('cancelled', 'Cancelled'), ('error', 'Error')], default='new', max_length=16),
        ),
    ]