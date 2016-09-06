from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^new$', views.new),
    url(r'^view/(?P<id>[0-9]+)$', views.view, name='view'),
    url(r'^cancel/(?P<id>[0-9]+)$', views.cancel, name='cancel'),
    url(r'^cancel_subscr/(?P<id>[0-9]+)$', views.cancel_subscr, name='cancel_subscr'),
    url(r'^return_subscr/(?P<id>[0-9]+)$', views.return_subscr, name='return_subscr'),

    url(r'^callback/paypal/(?P<id>[0-9]+)$', views.callback_paypal, name='cb_paypal'),
    url(r'^callback/stripe/(?P<id>[0-9]+)$', views.callback_stripe, name='cb_stripe'),
    url(r'^callback/coinbase/$', views.callback_coinbase, name='cb_coinbase'),
    url(r'^callback/paypal_subscr/(?P<id>[0-9]+)$', views.callback_paypal_subscr, name='cb_paypal_subscr'),
    url(r'^callback/stripe_subscr/(?P<id>[0-9]+)$', views.callback_stripe_subscr, name='cb_stripe_subscr'),

    url(r'^callback/stripe_hook$', views.stripe_hook, name='stripe_hook'),

    url(r'^$', views.list_payments),
]
