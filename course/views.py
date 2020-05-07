from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.template import loader


class CourseListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class CourseAPI(View):
    def get(self, request, course_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def put(self, request, course_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def delete(self, request, course_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class CourseInstanceListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class CourseInstanceAPI(View):
    def get(self, request, course_instance_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def put(self, request, course_instance_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def delete(self, request, course_instance_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class CourseHomeView(View):

    def get(self, request):
        template = loader.get_template('course/index.html')
        context = {}
        context['site_name'] = settings.SITE_NAME
        if request.user.is_authenticated:
            context['is_authenticated'] = True
            context['username'] = request.user.name
        else:
            context['is_authenticated'] = False
        test = template.render(context, request)
        return HttpResponse(template.render(context, request))
