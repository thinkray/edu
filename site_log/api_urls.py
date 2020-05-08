from django.urls import path

from . import views

urlpatterns = [
    path('list', views.LogListAPI.as_view(), name='log_list_api'),
    path('<int:log_id>', views.LogAPI.as_view(), name='log_api'),
]
