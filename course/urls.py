from django.urls import path

from . import views

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list_view'),
    path('<int:page>', views.CourseListView.as_view(), name='course_list_view_page'),
]
