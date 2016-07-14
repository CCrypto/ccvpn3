from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^login$', auth_views.login, name='login'),
    url(r'^logout$', views.logout, name='logout'),
    url(r'^signup$', views.signup, name='signup'),

    url(r'^settings', views.settings),
    url(r'^config_dl', views.config_dl),
    url(r'^config', views.config),
    url(r'^logs', views.logs),
    url(r'^gift_code', views.gift_code),
    url(r'^trial', views.trial),
    url(r'^', views.index, name='index'),
]
