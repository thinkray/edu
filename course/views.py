import json

from django.conf import settings
from django.core.validators import MinValueValidator
from django.forms import (
    BooleanField, CharField, DateTimeField, DecimalField, Form, IntegerField,
    MultipleChoiceField)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.utils.timezone import localtime
from django.views import View

from account.models import User
from storage.models import BlobStorage

from .models import Course, CourseInstance


class CourseListAPI(View):
    def get(self, request):
        class CourseListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("name", "name"),
                ("info", "info"),
                ("picture", "picture"),
                ("start_date", "start_date"),
                ("end_date", "end_date"),
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

            if cleaned_data['offset'] is None:
                cleaned_data['offset'] = 0
            if cleaned_data['limit'] is None:
                cleaned_data['limit'] = 10

            result = list(Course.objects.all()[
                          cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))

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
        class CourseAPIGetForm(Form):
            choices = (
                ("name", "name"),
                ("info", "info"),
                ("picture", "picture"),
                ("start_date", "start_date"),
                ("end_date", "end_date"),
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

        form = CourseAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                result = list(Course.objects.filter(pk=course_id).values(
                    'id', *cleaned_data['column']))
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            if result == []:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                    'data': [],
                }, status=404)

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

    def put(self, request, course_id):
        class CourseAPIPutForm(Form):
            name = CharField(max_length=200)
            info = CharField(required=False)
            start_date = DateTimeField()
            end_date = DateTimeField()
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

        form = CourseAPIPutForm(data)
        if form.is_valid():
            try:
                course = Course.objects.get(pk=course_id)
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            cleaned_data = form.clean()

            if cleaned_data['name'] != '':
                course.name = cleaned_data['name']

            if cleaned_data['info'] != '':
                course.info = cleaned_data['info']

            if cleaned_data['start_date'] != '':
                course.start_date = cleaned_data['start_date']

            if cleaned_data['end_date'] != '':
                course.end_date = cleaned_data['end_date']

            if cleaned_data['start_date'] > cleaned_data['end_date']:
                return JsonResponse({
                    'status': 400,
                    'message': 'InvalidDate',
                }, status=400)

            if cleaned_data['price'] != '':
                course.price = cleaned_data['price']

            if cleaned_data['quota'] != '':
                course.quota = cleaned_data['quota']

            if cleaned_data['sold'] is not None:
                course.sold = cleaned_data['sold']

            course.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success',
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def delete(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
        except Exception as e:
            return JsonResponse({
                'status': 404,
                'message': 'Not Found',
            }, status=404)

        course.delete()

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })


class CourseInstanceListAPI(View):
    def get(self, request):
        class CourseInstanceListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("course", "course"),
                ("student", "student"),
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

        form = CourseInstanceListAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            if cleaned_data['offset'] is None:
                cleaned_data['offset'] = 0
            if cleaned_data['limit'] is None:
                cleaned_data['limit'] = 10

            result = list(CourseInstance.objects.all()[
                          cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))

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
        class CourseInstanceListAPIPostForm(Form):
            course = IntegerField()
            student = IntegerField()

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = CourseInstanceListAPIPostForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                cleaned_data['course'] = Course.objects.get(
                    pk=cleaned_data['course'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'CourseNotFound',
                }, status=400)

            try:
                cleaned_data['student'] = User.objects.get(
                    pk=cleaned_data['student'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'StudentNotFound',
                }, status=400)

            course_instance = CourseInstance(
                course=cleaned_data['course'], student=cleaned_data['student'], quota=cleaned_data['course'].quota)
            course_instance.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success'
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)


class CourseInstanceAPI(View):
    def get(self, request, course_instance_id):
        class CourseInstanceAPIGetForm(Form):
            choices = (
                ("course", "course"),
                ("student", "student"),
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

        form = CourseInstanceAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                result = list(CourseInstance.objects.filter(pk=course_instance_id).values(
                    'id', *cleaned_data['column']))
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                    'data': [],
                }, status=404)

            if result == []:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                    'data': [],
                }, status=404)

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

    def patch(self, request, course_instance_id):
        class CourseInstanceAPIPatchForm(Form):
            quota = IntegerField(validators=[MinValueValidator(0)])

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = CourseInstanceAPIPatchForm(data)
        if form.is_valid():
            try:
                course_instance = CourseInstance.objects.get(
                    pk=course_instance_id)
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                    'data': [],
                }, status=404)

            cleaned_data = form.clean()

            if cleaned_data['quota'] != '':
                course_instance.quota = cleaned_data['quota']

            course_instance.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success',
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def delete(self, request, course_instance_id):
        try:
            course_instance = CourseInstance.objects.get(pk=course_instance_id)
        except Exception as e:
            return JsonResponse({
                'status': 404,
                'message': 'Not Found',
            }, status=404)

        course_instance.delete()

        return JsonResponse({
            'status': 200,
            'message': 'Success',
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
