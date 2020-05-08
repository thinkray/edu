from django.urls import path

from . import views

urlpatterns = [
    path('bill/list', views.BillListAPI.as_view(), name='bill_list_api'),
    path('bill/<int:bill_id>', views.BillAPI.as_view(), name='bill_api'),
    path('redemption_code/redeem', views.RedeemRedemptionCodeAPI.as_view(),
         name='redeem_redemption_code_api'),
    path('redemption_code/list', views.RedemptionCodeListAPI.as_view(),
         name='redemption_code_list_api'),
    path('redemption_code/<int:redemption_code_id>',
         views.RedemptionCodeAPI.as_view(), name='redemption_code_api'),
    path('coupon_code/list', views.CouponCodeListAPI.as_view(),
         name='coupon_code_list_api'),
    path('coupon_code/check', views.CouponCodeCheckAPI.as_view(),
         name='coupon_code_check_api'),
    path('coupon_code/<int:coupon_code_id>',
         views.CouponCodeAPI.as_view(), name='coupon_code_api'),
]
