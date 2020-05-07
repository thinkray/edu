from django.urls import path

from . import views

urlpatterns = [
    path('list', views.UserListAPI.as_view(), name='user_list_api'),
    path('login', views.UserLoginAPI.as_view(), name='user_login_api'),
    path('logout', views.UserLogoutAPI.as_view(), name='user_logout_api'),
    path('<int:user_id>', views.UserAPI.as_view(), name='user_api'),
]
