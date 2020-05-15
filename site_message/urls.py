from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='inbox'), name='message_redirect_view'),
    path('send', views.MessageSendView.as_view(), name='message_send_view'),
    path('<int:message_id>', views.MessageDetailView.as_view(), name='message_detail_view'),
    path('<str:box_name>/', views.MessageView.as_view(), name='message_view_box'),
    path('<str:box_name>/<int:page>', views.MessageView.as_view(), name='message_view_page'),
]
