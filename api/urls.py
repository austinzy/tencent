from django.urls import include
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^get_ins_info/$', views.GetInstanceInfo.as_view(), name='get_ins_info'),
    url(r'^get_user_ins_info/$', views.GetUserInstanceInfo.as_view(), name='get_user_ins_info'),
    url(r'^create_ins/$', views.CreateInstance.as_view(), name='create_ins'),

    url(r'^auth/', include('rest_auth.urls')),
]
