from django.conf.urls import url
from webopenface import api_views
from webopenface.api_views import one_time_startup

urlpatterns = [
    url(r'^onmessage/$', api_views.on_message, name='onMessage'),
    # url(r'^onmessage/$', api_views.on_message, name='onMessage'),
    # url(r'^preview/$', views.preview, name='preview'),
    # url(r'^person/$', views.person, name='person'),
]

one_time_startup()
