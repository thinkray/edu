from django.urls import path

from . import views

urlpatterns = [
    path('', views.CourseHomeView.as_view(), name='course_home_view'),
]
