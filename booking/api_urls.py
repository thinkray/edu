from django.urls import path

from . import views

urlpatterns = [
    path('list', views.BookingListAPI.as_view(), name='booking_list_api'),
    path('<int:booking_id>', views.BookingAPI.as_view(), name='booking_api'),
]
