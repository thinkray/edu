from django.urls import path

from . import views

urlpatterns = [
    path('list', views.MessageListAPI.as_view(), name='message_list_api'),
    path('<int:message_id>', views.MessageAPI.as_view(), name='message_api'),
]
