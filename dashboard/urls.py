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
    path('admin/user/', views.AdminUserListView.as_view(), name='admin_user_list_view'),
    path('admin/user/<int:page>', views.AdminUserListView.as_view(), name='admin_user_list_view_page'),
    path('admin/code/coupon/', views.AdminCouponCodeListView.as_view(), name='admin_coupon_code_list_view'),
    path('admin/code/coupon/<int:page>', views.AdminCouponCodeListView.as_view(), name='admin_coupon_code_list_view_page'),
    path('admin/code/redemption/', views.AdminRedemptionCodeListView.as_view(), name='admin_redemption_code_list_view'),
    path('admin/code/redemption/<int:page>', views.AdminRedemptionCodeListView.as_view(), name='admin_redemption_code_list_view_page'),
]