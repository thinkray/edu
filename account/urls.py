from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='user_login_view'),
    path('signup/', views.UserSignupView.as_view(), name='user_signup_view'),
    path('<int:user_id>/', views.UserProfileView.as_view(), name='user_profile_view'),
]
