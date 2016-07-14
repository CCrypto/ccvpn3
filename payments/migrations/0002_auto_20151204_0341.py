# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recurringpaymentsource',
            name='period',
            field=models.CharField(max_length=16, choices=[('6m', 'Every 6 months'), ('1year', 'Yearly')]),
        ),
    ]
