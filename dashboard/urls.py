from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path('', views.UserOverviewView.as_view(), name='user_overview_view'),
    path('bill/', views.UserBillListView.as_view(), name='bill_list_view'),
    path('bill/<int:page>', views.UserBillListView.as_view(), name='bill_list_view_page'),
    path('calendar/', views.UserCalendarView.as_view(), name='user_calendar_list_view'),
    path('course/', RedirectView.as_view(url='study'), name='user_course_redirect_view'),
    path('course/<str:panel_name>/', views.UserCourseView.as_view(), name='user_course_view_panel'),
    path('course/<str:panel_name>/<int:page>', views.UserCourseView.as_view(), name='user_course_view_panel_page'),
    path('profile/', views.UserProfileEditView.as_view(), name='user_profile_edit_view'),
    path('log/', views.UserLogListView.as_view(), name='user_log_list_view'),
    path('log/<int:page>', views.UserLogListView.as_view(), name='user_log_list_view_page'),
    path('admin/', views.AdminOverviewView.as_view(), name='admin_overview_view'),
    path('admin/balance/', views.AdminBalanceListView.as_view(), name='admin_balance_list_view'),
    path('admin/balance/<int:page>', views.AdminBalanceListView.as_view(), name='admin_balance_list_view_page'),
    path('admin/calendar/', views.AdminCalendarView.as_view(), name='admin_calendar_list_view'),
    path('admin/course/', views.AdminCourseView.as_view(), name='admin_course_view'),
    path('admin/course/<int:page>', views.AdminCourseView.as_view(), name='admin_course_view_page'),
    path('admin/user/', views.AdminUserListView.as_view(), name='admin_user_list_view'),
    path('admin/user/<int:page>', views.AdminUserListView.as_view(), name='admin_user_list_view_page'),
    path('admin/bill/', views.AdminBillListView.as_view(), name='admin_bill_list_view'),
    path('admin/bill/<int:page>', views.AdminBillListView.as_view(), name='admin_bill_list_view_page'),
    path('admin/code/coupon/', views.AdminCouponCodeListView.as_view(), name='admin_coupon_code_list_view'),
    path('admin/code/coupon/<int:page>', views.AdminCouponCodeListView.as_view(), name='admin_coupon_code_list_view_page'),
    path('admin/code/redemption/', views.AdminRedemptionCodeListView.as_view(), name='admin_redemption_code_list_view'),
    path('admin/code/redemption/<int:page>', views.AdminRedemptionCodeListView.as_view(), name='admin_redemption_code_list_view_page'),
    path('admin/log/', views.AdminLogListView.as_view(), name='admin_log_list_view'),
    path('admin/log/<int:page>', views.AdminLogListView.as_view(), name='admin_log_list_view_page'),
]
