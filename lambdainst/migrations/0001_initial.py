# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import lambdainst.models
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GiftCode',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('code', models.CharField(default=lambdainst.models.random_gift_code, max_length=32)),
                ('time', models.DurationField(default=datetime.timedelta(30))),
                ('created', models.DateTimeField(null=True, auto_now_add=True)),
                ('single_use', models.BooleanField(default=True)),
                ('free_only', models.BooleanField(default=True)),
                ('available', models.BooleanField(default=True)),
                ('comment', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(related_name='created_giftcode_set', null=True, blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Gift Codes',
                'verbose_name': 'Gift Code',
            },
        ),
        migrations.CreateModel(
            name='GiftCodeUser',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('date', models.DateTimeField(null=True, auto_now_add=True)),
                ('code', models.ForeignKey(to='lambdainst.GiftCode')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Gift Code Users',
                'verbose_name': 'Gift Code User',
            },
        ),
        migrations.CreateModel(
            name='VPNUser',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('notes', models.TextField(blank=True)),
                ('expiration', models.DateTimeField(null=True, blank=True)),
                ('last_expiry_notice', models.DateTimeField(null=True, blank=True)),
                ('notify_expiration', models.BooleanField(default=True)),
                ('trial_periods_given', models.IntegerField(default=0)),
                ('last_vpn_auth', models.DateTimeField(null=True, blank=True)),
                ('referrer_used', models.BooleanField(default=False)),
                ('referrer', models.ForeignKey(related_name='referrals', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'VPN Users',
                'verbose_name': 'VPN User',
            },
        ),
        migrations.AddField(
            model_name='giftcode',
            name='users',
            field=models.ManyToManyField(through='lambdainst.GiftCodeUser', to=settings.AUTH_USER_MODEL),
        ),
    ]
