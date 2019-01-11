from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^chooser/(?P<app_label>[a-zA-Z0-9_]+)/(?P<model_name>[a-zA-Z0-9_]+)/$',
        views.chooser,
        name='model_chooser'),
    url(r'^chooser/(?P<app_label>[a-zA-Z0-9_]+)/(?P<model_name>[a-zA-Z0-9_]+)/(?P<filter_name>.+)/$',
        views.chooser,
        name='model_chooser'),

    # UUID
    url(r'^chooser/(?P<signed_data>[a-zA-Z0-9.:_-]+)/$',
        views.chooser,
        name='model_chooser'),
]
