from django.conf.urls import url, include

from . import views
from .api.v1.routers import router

app_name = 'budget'

urlpatterns = [
    url(r'^ofx_upload/$', views.ofx_upload_view, name='ofx_upload'),
    url(r'^api/v1/', include(router.urls)),
    #url(r'^api/v1/', include(
    #     'rest_framework.urls', 
    #     namespace='rest_framework')
    #)
]