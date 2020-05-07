from django.views import View
from django.shortcuts import render
from django.http import JsonResponse


class BillListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class BillAPI(View):
    def get(self, request, bill_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def put(self, request, bill_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def delete(self, request, bill_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class RedeemRedemptionCodeAPI(View):

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class RedemptionCodeListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class RedemptionCodeAPI(View):
    def get(self, request, redemption_code_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def patch(self, request, redemption_code_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def delete(self, request, redemption_code_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class CouponCodeListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class CouponCodeAPI(View):
    def get(self, request, coupon_code_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def delete(self, request, coupon_code_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })
