from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^new$', views.new),
    url(r'^view/(?P<id>[0-9]+)$', views.view, name='view'),
    url(r'^cancel/(?P<id>[0-9]+)$', views.cancel, name='cancel'),

    url(r'^callback/paypal/(?P<id>[0-9]+)$', views.callback_paypal, name='cb_paypal'),
    url(r'^callback/stripe/(?P<id>[0-9]+)$', views.callback_stripe, name='cb_stripe'),
    url(r'^callback/coinbase/$', views.callback_coinbase, name='cb_coinbase'),

    url(r'^$', views.list_payments),
]
