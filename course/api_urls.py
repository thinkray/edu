from django.urls import path

from . import views

urlpatterns = [
    path('list/', views.CourseListAPI.as_view(), name='course_list_api'),
    path('<int:course_id>/', views.CourseAPI.as_view(), name='course_api'),
    path('instance/list/', views.CourseInstanceListAPI.as_view(),
         name='course_instance_list_api'),
    path('instance/<int:course_instance_id>/',
         views.CourseInstanceAPI.as_view(), name='course_instance_api'),
]
