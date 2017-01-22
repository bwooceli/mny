from django.conf.urls import url

from . import views

app_name = 'budget'

urlpatterns = [
    url(r'^ofx_upload/$', views.ofx_upload_view, name='ofx_upload'),
]