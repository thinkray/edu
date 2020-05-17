from django.urls import path

from . import views

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list_view'),
    path('<int:page>', views.CourseListView.as_view(), name='course_list_view_page'),
    path('detail/<int:course_id>', views.CourseDetailView.as_view(), name='course_detail_view_page'),
    path('detail/<int:course_id>/enroll', views.CourseEnrollView.as_view(), name='course_enroll_view_page'),
]
