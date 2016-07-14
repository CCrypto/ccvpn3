# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('category', models.CharField(max_length=16, choices=[('support', 'Support'), ('security', 'Security'), ('billing', 'Account / Billing')])),
                ('subject', models.CharField(max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('is_open', models.BooleanField(default=True)),
                ('closed', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'ordering': ('-created',),
                'permissions': (('view_any_ticket', 'Can view any ticket'), ('reply_any_ticket', 'Can reply to any ticket'), ('view_private_message', 'Can view private messages on tickets'), ('post_private_message', 'Can post private messages on tickets')),
            },
        ),
        migrations.CreateModel(
            name='TicketMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('remote_addr', models.GenericIPAddressField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('message', models.TextField()),
                ('staff_only', models.BooleanField(default=False)),
                ('ticket', models.ForeignKey(related_name='message_set', to='tickets.Ticket')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
        ),
        migrations.CreateModel(
            name='TicketNotifyAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('category', models.CharField(max_length=16, choices=[('support', 'Support'), ('security', 'Security'), ('billing', 'Account / Billing')])),
                ('address', models.EmailField(max_length=254)),
            ],
        ),
    ]
