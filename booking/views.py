from django.views import View
from django.shortcuts import render
from django.http import JsonResponse


class BookingListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class BookingAPI(View):
    def get(self, request, booking_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def put(self, request, booking_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def patch(self, request, booking_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def delete(self, request, booking_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })
