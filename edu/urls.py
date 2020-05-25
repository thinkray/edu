"""edu URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from course.views import CourseHomeView

urlpatterns = [
    path('', CourseHomeView.as_view(), name='home'),
    path('<int:page>', CourseHomeView.as_view(), name='home_page'),
    path('dashboard/', include('dashboard.urls')),
    path('user/', include('account.urls')),
    path('course/', include('course.urls')),
    path('message/', include('site_message.urls')),
    path('api/v1/account/', include('account.api_urls')),
    path('api/v1/booking/', include('booking.api_urls')),
    path('api/v1/course/', include('course.api_urls')),
    path('api/v1/finance/', include('finance.api_urls')),
    path('api/v1/log/', include('site_log.api_urls')),
    path('api/v1/message/', include('site_message.api_urls')),
]
