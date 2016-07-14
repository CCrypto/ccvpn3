# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('backend_id', models.CharField(choices=[('bitcoin', 'Bitcoin'), ('coinbase', 'Coinbase'), ('manual', 'Manual'), ('paypal', 'PayPal'), ('stripe', 'Stripe')], max_length=16)),
                ('status', models.CharField(choices=[('new', 'Waiting for payment'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('rejected', 'Rejected by processor'), ('error', 'Payment processing failed')], max_length=16)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('confirmed_on', models.DateTimeField(null=True, blank=True)),
                ('amount', models.IntegerField()),
                ('paid_amount', models.IntegerField(default=0)),
                ('time', models.DurationField()),
                ('status_message', models.TextField(null=True, blank=True)),
                ('backend_extid', models.CharField(null=True, max_length=64, blank=True)),
                ('backend_data', jsonfield.fields.JSONField(blank=True, default=dict)),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='RecurringPaymentSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('backend', models.CharField(choices=[('bitcoin', 'Bitcoin'), ('coinbase', 'Coinbase'), ('manual', 'Manual'), ('paypal', 'PayPal'), ('stripe', 'Stripe')], max_length=16)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('period', models.CharField(choices=[('monthly', 'Monthly'), ('biannually', 'Bianually'), ('yearly', 'Yearly')], max_length=16)),
                ('last_confirmed_payment', models.DateTimeField(null=True, blank=True)),
                ('backend_id', models.CharField(null=True, max_length=64, blank=True)),
                ('backend_data', jsonfield.fields.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='payment',
            name='recurring_source',
            field=models.ForeignKey(null=True, to='payments.RecurringPaymentSource', blank=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
