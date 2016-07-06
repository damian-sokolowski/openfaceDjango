from django.conf.urls import include, url
from webopenface import views

urlpatterns = [
    url(r'^api/', include('webopenface.api_urls')),
    url(r'^$', views.index, name='index'),
    url(r'^preview/$', views.preview, name='preview'),
    url(r'^person/$', views.person, name='person'),
    url(r'^lastframes/$', views.last_frames, name='lastFrames'),
    url(r'^detectedpeople/(?P<pk>[0-9])$', views.detected_people, name='detectedPeople'),
]
