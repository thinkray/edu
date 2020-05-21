from django.urls import path

from . import views

urlpatterns = [
    # ex: /polls/
    #path('', views.index, name='index'),
    # ex: /polls/5/
    #path('<int:question_id>/', views.detail, name='detail'),
    # ex: /polls/5/results/
    #path('<int:question_id>/results/', views.results, name='results'),
    # ex: /polls/5/vote/
    #path('<int:question_id>/vote/', views.vote, name='vote'),
    path('bill/', views.UserBillListView.as_view(), name='bill_list_view'),
    path('bill/<int:page>', views.UserBillListView.as_view(), name='bill_list_view_page'),
    path('calendar/', views.UserCalendarView.as_view(), name='user_calendar_list_view'),
    path('log/', views.UserLogListView.as_view(), name='user_log_list_view'),
    path('log/<int:page>', views.UserLogListView.as_view(), name='user_log_list_view_page'),
    path('admin/balance/', views.AdminBalanceListView.as_view(), name='admin_balance_list_view'),
    path('admin/balance/<int:page>', views.AdminBalanceListView.as_view(), name='admin_balance_list_view_page'),
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