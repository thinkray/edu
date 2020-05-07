from django.views import View
from django.shortcuts import render
from django.http import JsonResponse


class MessageListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class MessageAPI(View):
    def get(self, request, message_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def patch(self, request, message_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def delete(self, request, message_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })
