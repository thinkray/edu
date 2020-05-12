import json

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import transaction
from django.forms import (BooleanField, CharField, ChoiceField, DateTimeField,
                          DecimalField, Form, IntegerField,
                          MultipleChoiceField)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.utils.timezone import localtime, now
from django.views import View

from account.models import User
from finance.models import Bill, CouponCode
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
        if not request.user.is_superuser and not request.user.groups.filter(name='teacher').exists():
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class CourseListAPIPostForm(Form):
            name = CharField(max_length=200)
            info = CharField(required=False)
            start_date = DateTimeField()
            end_date = DateTimeField()
            teacher = IntegerField(required=False)
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

            if request.user.is_superuser and 'teacher' in data:
                try:
                    cleaned_data['teacher'] = User.objects.get(
                        pk=cleaned_data['teacher'])
                except Exception as e:
                    return JsonResponse({
                        'status': 400,
                        'message': 'TeacherNotFound',
                    }, status=400)
            else:
                cleaned_data['teacher'] = request.user

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

            if not request.user.is_superuser and course.teacher != request.user:
                return JsonResponse({
                    'status': 403,
                    'message': 'Forbidden'
                }, status=403)

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

        if not request.user.is_superuser and course.teacher != request.user:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        course.delete()

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })


class CourseInstanceListAPI(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class CourseInstanceListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("course", "course"),
                ("student", "student"),
                ("teacher", "teacher"),
                ("quota", "quota"),
            )
            column = MultipleChoiceField(choices=choices)
            panel_choices = (
                ("teacher", "teacher"),
                ("student", "student"),
                ("all", "all"),
            )
            panel = ChoiceField(choices=panel_choices)

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

            result = []
            if cleaned_data['panel'] == 'all':
                if request.user.is_superuser:
                    result = list(CourseInstance.objects.all()[
                        cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))
                else:
                    return JsonResponse({
                        'status': 403,
                        'message': 'Forbidden'
                    }, status=403)
            elif cleaned_data['panel'] == 'teacher':
                if request.user.groups.filter(name='teacher').exists() or request.user.is_superuser:
                    result = list(CourseInstance.objects.filter(teacher=request.user)[
                        cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))
                else:
                    return JsonResponse({
                        'status': 403,
                        'message': 'Forbidden'
                    }, status=403)
            elif cleaned_data['panel'] == 'student':
                result = result + list(CourseInstance.objects.filter(student=request.user)[
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
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class CourseInstanceListAPIPostForm(Form):
            course = IntegerField()
            coupon_code = CharField(required=False)

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

            if cleaned_data['coupon_code'] != '':
                try:
                    coupon_code_discount = CouponCode.objects.get(
                        code=cleaned_data['coupon_code']).discount
                except Exception as e:
                    return JsonResponse({
                        'status': 400,
                        'message': 'CouponCodeNotFound',
                    }, status=400)
            else:
                coupon_code_discount = 0

            need_to_pay = round(
                cleaned_data['course'].price * (1-coupon_code_discount), 2)
            if request.user.balance < need_to_pay:
                return JsonResponse({
                    'status': 403,
                    'message': 'InsufficientBalance',
                }, status=403)

            try:
                with transaction.atomic():
                    bill = Bill(user=request.user, amount=-need_to_pay, date=now(
                    ), info='Pay for the course '+cleaned_data['course'].name)
                    request.user.balance = request.user.balance - need_to_pay
                    course_instance = CourseInstance(
                        course=cleaned_data['course'], student=request.user, teacher=cleaned_data['course'].teacher, quota=cleaned_data['course'].quota)

                    bill.save()
                    request.user.save()
                    course_instance.save()
            except Exception as e:
                return JsonResponse({
                    'status': 500,
                    'message': 'DatabaseError',
                }, status=500)

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
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class CourseInstanceAPIGetForm(Form):
            choices = (
                ("course", "course"),
                ("student", "student"),
                ("teacher", "teacher"),
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
            query_data = cleaned_data['column'].copy()
            if not 'student' in cleaned_data['column']:
                query_data.append('student')
            if not 'teacher' in cleaned_data['column']:
                query_data.append('teacher')

            try:
                result = list(CourseInstance.objects.filter(pk=course_instance_id).values(
                    'id', *query_data))
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

            if result[0]['student'] != request.user.id and result[0]['teacher'] != request.user.id and not request.user.is_superuser:
                return JsonResponse({
                    'status': 403,
                    'message': 'Forbidden'
                }, status=403)

            if not 'student' in cleaned_data['column']:
                for each in result:
                    del each['student']
            if not 'teacher' in cleaned_data['column']:
                for each in result:
                    del each['teacher']

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
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

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
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

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
