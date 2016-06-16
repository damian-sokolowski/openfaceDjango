from django.conf.urls import url

from webopenface import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^preview/$', views.preview, name='preview'),
    url(r'^person/$', views.person, name='person'),
]