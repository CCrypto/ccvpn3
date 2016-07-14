from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^new$', views.new, name='new'),
    url(r'^view/(?P<id>[0-9]+)$', views.view, name='view'),
    url(r'^$', views.index, name='index'),
    url(r'^open$', views.index, dict(f='open'), name='index_open'),
    url(r'^closed$', views.index, dict(f='closed'), name='index_closed'),
    url(r'^all_open$', views.index, dict(f='open', all=True), name='index_open_all'),
    url(r'^all_closed$', views.index, dict(f='closed', all=True), name='index_closed_all'),
]

