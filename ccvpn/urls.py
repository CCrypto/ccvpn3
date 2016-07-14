from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from . import views

from lambdainst import urls as account_urls, views as account_views
from payments import urls as payments_urls
from tickets import urls as tickets_urls

urlpatterns = [
    url(r'^admin/status$', account_views.admin_status, name='admin_status'),
    url(r'^admin/referrers$', account_views.admin_ref, name='admin_ref'),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^api/auth$', account_views.api_auth),

    url(r'^$', views.index, name='index'),
    url(r'^ca.crt$', account_views.ca_crt),
    url(r'^setlang$', views.set_lang, name='set_lang'),
    url(r'^chat$', views.chat, name='chat'),
    url(r'^page/(?P<name>[a-zA-Z0-9_-]+)$', views.page, name='page'),
    url(r'^status$', account_views.status),

    url(r'^account/forgot$', auth_views.password_reset,
        {}, name='password_reset'),
    url(r'^account/forgot_done$', auth_views.password_reset_done,
        name='password_reset_done'),
    url(r'^account/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^account/reset/done/$', auth_views.password_reset_complete,
        name='password_reset_complete'),

    url(r'^account/', include(account_urls, namespace='account')),
    url(r'^payments/', include(payments_urls, namespace='payments')),
    url(r'^tickets/', include(tickets_urls, namespace='tickets')),

]
