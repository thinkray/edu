from django.views import View
from django.shortcuts import render
from django.http import JsonResponse


class LogListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class LogAPI(View):
    def get(self, request, log_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })
