from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.forms import Form, CharField, BooleanField, DecimalField, IntegerField, DateTimeField, MultipleChoiceField
from django.conf import settings
from django.template import loader
from django.core.validators import MinValueValidator
from django.utils.timezone import localtime
from .models import Course, CourseInstance
from account.models import User
from storage.models import BlobStorage
import json


class CourseListAPI(View):
    def get(self, request):
        class CourseListAPIGetForm(Form):
            id_start = IntegerField(initial=1, required=False)
            id_end = IntegerField(initial=10, required=False)
            choices = (
                ("name", "name"),
                ("info", "info"),
                ("picture", "picture"),
                ("start_date", "start date"),
                ("end_date", "end date"),
                ("teacher", "teacher"),
                ("price", "price"),
                ("quota", "quota"),
            )
            column = MultipleChoiceField(choices=choices)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = CourseListAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            if cleaned_data['id_start'] is None and cleaned_data['id_end'] is not None:
                cleaned_data['id_start'] = cleaned_data['id_end'] - 10
            else:
                cleaned_data['id_start'] = 1
            if cleaned_data['id_end'] is None:
                cleaned_data['id_end'] = cleaned_data['id_start'] + 10

            result = list(Course.objects.filter(id__range=[
                          cleaned_data['id_start'], cleaned_data['id_end']]).values('id', *cleaned_data['column']))

            if 'start_date' in cleaned_data['column']:
                for each in result:
                    each['start_date'] = localtime(each['start_date'])

            if 'end_date' in cleaned_data['column']:
                for each in result:
                    each['end_date'] = localtime(each['end_date'])

            return JsonResponse({
                'status': 200,
                'message': 'Success',
                'data': result,
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def post(self, request):
        class CourseListAPIPostForm(Form):
            name = CharField(max_length=200)
            info = CharField(required=False)
            start_date = DateTimeField()
            end_date = DateTimeField()
            teacher = IntegerField()
            price = DecimalField(max_digits=10, decimal_places=2)
            quota = IntegerField(validators=[MinValueValidator(0)])
            sold = IntegerField(
                validators=[MinValueValidator(0)], required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = CourseListAPIPostForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                cleaned_data['teacher'] = User.objects.get(
                    pk=cleaned_data['teacher'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'TeacherNotFound',
                }, status=400)

            if cleaned_data['sold'] is None:
                cleaned_data['sold'] = 0

            course = Course(name=cleaned_data['name'], info=cleaned_data['info'], start_date=cleaned_data['start_date'], end_date=cleaned_data['end_date'],
                            teacher=cleaned_data['teacher'], price=cleaned_data['price'], quota=cleaned_data['quota'], sold=cleaned_data['sold'])
            course.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success'
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)


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
