import base64
import json

from django.conf import settings
from django.core.paginator import Paginator
from django.core.validators import MinValueValidator
from django.db import transaction
from django.db.models import Q
from django.forms import (BooleanField, CharField, ChoiceField, DateTimeField,
                          DecimalField, FileField, Form, IntegerField,
                          MultipleChoiceField)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse
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

        form = CourseListAPIGetForm(request.GET)
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
            teacher = CharField(required=False)
            price = DecimalField(max_digits=10, decimal_places=2)
            quota = IntegerField(validators=[MinValueValidator(0)])
            sold = IntegerField(
                validators=[MinValueValidator(0)], required=False)
            picture = FileField(required=False)

        form = CourseListAPIPostForm(request.POST, request.FILES)
        if form.is_valid():
            cleaned_data = form.clean()

            if request.user.is_superuser and 'teacher' in request.POST:
                try:
                    cleaned_data['teacher'] = User.objects.get(
                        username=cleaned_data['teacher'])
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

            if cleaned_data['picture'] is not None:
                if cleaned_data['picture'].content_type[:5] != 'image':
                    return JsonResponse({
                        'status': 400,
                        'message': 'IllegalFileType'
                    }, status=400)
                try:
                    with transaction.atomic():
                        blob_storage = BlobStorage(data=cleaned_data['picture'].file.read(
                        ), content_type=cleaned_data['picture'].content_type)
                        blob_storage.save()
                        course.picture = blob_storage
                        course.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)

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

        form = CourseAPIGetForm(request.GET)
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

    def post(self, request, course_id):
        class CourseAPIPostForm(Form):
            name = CharField(max_length=200)
            info = CharField(required=False)
            start_date = DateTimeField()
            end_date = DateTimeField()
            price = DecimalField(max_digits=10, decimal_places=2)
            quota = IntegerField(validators=[MinValueValidator(0)])
            sold = IntegerField(
                validators=[MinValueValidator(0)], required=False)
            picture = FileField(required=False)

        form = CourseAPIPostForm(request.POST, request.FILES)
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

            if cleaned_data['picture'] is not None:
                if cleaned_data['picture'].content_type[:5] != 'image':
                    return JsonResponse({
                        'status': 400,
                        'message': 'IllegalFileType'
                    }, status=400)
                if course.picture is None:
                    try:
                        with transaction.atomic():
                            blob_storage = BlobStorage(data=cleaned_data['picture'].file.read(
                            ), content_type=cleaned_data['picture'].content_type)
                            blob_storage.save()
                            course.picture = blob_storage
                            course.save()
                    except Exception as e:
                        return JsonResponse({
                            'status': 500,
                            'message': 'DatabaseError',
                        }, status=500)
                else:
                    try:
                        with transaction.atomic():
                            course.picture.data = cleaned_data['picture'].file.read(
                            )
                            course.picture.content_type = cleaned_data['picture'].content_type
                            course.picture.save()
                            course.save()
                    except Exception as e:
                        return JsonResponse({
                            'status': 500,
                            'message': 'DatabaseError',
                        }, status=500)

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

        try:
            with transaction.atomic():
                if course.picture is not None:
                    course.picture.delete()
                course.delete()
        except Exception as e:
            return JsonResponse({
                'status': 500,
                'message': 'DatabaseError',
            }, status=500)

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
                    cleaned_data['course'].sold += 1

                    bill.save()
                    request.user.save()
                    course_instance.save()
                    cleaned_data['course'].save()
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

    def get(self, request, page=1):

        context = {}
        result = Course.objects.all()
        context['page_name'] = 'Home'

        paginator = Paginator(result, 9)
        page_obj = paginator.get_page(page)

        template = loader.get_template('course/index.html')

        context['site_name'] = settings.SITE_NAME

        if request.user.is_authenticated:
            context['is_authenticated'] = True
            context['is_superuser'] = request.user.is_superuser
            context['is_teacher'] = request.session.get('is_teacher')
            context['name'] = request.user.name
            context['username'] = request.user.username
        else:
            context['is_authenticated'] = False
            context['is_superuser'] = False

        context['page_obj'] = page_obj
        course_set = []
        for each in page_obj:
            if each.picture is not None:
                current_item = {'picture': 'data:' + each.picture.content_type +
                                ';base64,' +
                                str(base64.b64encode(each.picture.data), encoding='utf-8')}
            else:
                current_item = {'picture': ''}

            current_item['id'] = each.id
            current_item['name'] = each.name
            current_item['teacher_id'] = each.teacher.id
            current_item['teacher_name'] = each.teacher.name
            current_item['info'] = each.info
            current_item['start_date'] = each.start_date
            current_item['end_date'] = each.end_date
            current_item['price'] = each.price
            current_item['quota'] = each.quota
            current_item['sold'] = each.sold
            course_set.append(current_item)
        context['course_set'] = course_set

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num/2)):
            if page_start-1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num/2)*2):
            if page_end+1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end-page_start < int(page_bar_num/2)*2:
            for i in range(int(page_bar_num/2)*2):
                if page_start-1 >= 1 and page_end-page_start < int(page_bar_num/2)*2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end+1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))


class CourseListView(View):

    def get(self, request, page=1):

        context = {}
        result = Course.objects.all()
        context['page_name'] = 'Course List'

        paginator = Paginator(result, 9)
        page_obj = paginator.get_page(page)

        template = loader.get_template('course/course_list.html')

        context['site_name'] = settings.SITE_NAME

        if request.user.is_authenticated:
            context['is_authenticated'] = True
            context['is_superuser'] = request.user.is_superuser
            context['is_teacher'] = request.session.get('is_teacher')
            context['name'] = request.user.name
            context['username'] = request.user.username
        else:
            context['is_authenticated'] = False
            context['is_superuser'] = False

        context['page_obj'] = page_obj
        course_set = []
        for each in page_obj:
            if each.picture is not None:
                current_item = {'picture': 'data:' + each.picture.content_type +
                                ';base64,' +
                                str(base64.b64encode(each.picture.data), encoding='utf-8')}
            else:
                current_item = {'picture': ''}

            current_item['id'] = each.id
            current_item['name'] = each.name
            current_item['teacher_id'] = each.teacher.id
            current_item['teacher_name'] = each.teacher.name
            current_item['info'] = each.info
            current_item['start_date'] = each.start_date
            current_item['end_date'] = each.end_date
            current_item['price'] = each.price
            current_item['quota'] = each.quota
            current_item['sold'] = each.sold
            course_set.append(current_item)
        context['course_set'] = course_set

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num/2)):
            if page_start-1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num/2)*2):
            if page_end+1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end-page_start < int(page_bar_num/2)*2:
            for i in range(int(page_bar_num/2)*2):
                if page_start-1 >= 1 and page_end-page_start < int(page_bar_num/2)*2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end+1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))


class CourseDetailView(View):

    def get(self, request, course_id=1):

        context = {}
        context['status'] = 200
        try:
            course = Course.objects.get(pk=course_id)
            context['course'] = course
            if course.picture:
                context['picture'] = 'data:' + course.picture.content_type + \
                    ';base64,' + \
                    str(base64.b64encode(course.picture.data), encoding='utf-8')
            else:
                context['picture'] = ''
        except Exception as e:
            context['status'] = 404
            context['message'] = 'CourseNotFound'

        context['page_name'] = 'Course Detail'

        template = loader.get_template('course/course_detail.html')

        context['site_name'] = settings.SITE_NAME

        if request.user.is_authenticated:
            context['is_authenticated'] = True
            context['is_superuser'] = request.user.is_superuser
            context['is_teacher'] = request.session.get('is_teacher')
            context['name'] = request.user.name
            context['username'] = request.user.username

        else:
            context['is_authenticated'] = False
            context['is_superuser'] = False

        context['hide_welcome'] = True

        return HttpResponse(template.render(context, request))


class CourseEnrollView(View):

    def get(self, request, course_id=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        context = {}
        context['status'] = 200
        try:
            course = Course.objects.get(pk=course_id)
            context['course'] = course
        except Exception as e:
            context['status'] = 404
            context['message'] = 'CourseNotFound'

        context['page_name'] = 'Course Detail'

        template = loader.get_template('course/course_enroll.html')

        context['site_name'] = settings.SITE_NAME

        if request.user.is_authenticated:
            context['is_authenticated'] = True
            context['is_superuser'] = request.user.is_superuser
            context['is_teacher'] = request.session.get('is_teacher')
            context['name'] = request.user.name
            context['username'] = request.user.username
            context['balance'] = request.user.balance

        else:
            context['is_authenticated'] = False
            context['is_superuser'] = False

        context['hide_welcome'] = True

        return HttpResponse(template.render(context, request))


class CourseSearchView(View):

    def get(self, request, page=1):
        context = {}
        query = ""
        if request.GET:
            query = request.GET['q']
            context['query'] = str(query)

        result = Course.objects.all().filter(Q(name__icontains=query) |
                                             Q(info__icontains=query))

        context['course_search_num'] = len(result)
        context['page_name'] = 'Course Search Result'

        template = loader.get_template('course/course_search.html')

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        context['site_name'] = settings.SITE_NAME

        if request.user.is_authenticated:
            context['is_authenticated'] = True
            context['is_superuser'] = request.user.is_superuser
            context['is_teacher'] = request.session.get('is_teacher')
            context['name'] = request.user.name
            context['username'] = request.user.username
        else:
            context['is_authenticated'] = False
            context['is_superuser'] = False

        context['page_obj'] = page_obj

        course_set = []
        for each in page_obj:
            if each.picture is not None:
                current_item = {'picture': 'data:' + each.picture.content_type +
                                ';base64,' +
                                str(base64.b64encode(each.picture.data), encoding='utf-8')}
            else:
                current_item = {'picture': ''}

            current_item['id'] = each.id
            current_item['name'] = each.name
            current_item['teacher_id'] = each.teacher.id
            current_item['teacher_name'] = each.teacher.name
            current_item['info'] = each.info
            current_item['start_date'] = each.start_date
            current_item['end_date'] = each.end_date
            current_item['price'] = each.price
            current_item['quota'] = each.quota
            current_item['sold'] = each.sold
            course_set.append(current_item)
        context['course_set'] = course_set

        context['query'] = str(query)

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num / 2)):
            if page_start - 1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num / 2) * 2):
            if page_end + 1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end - page_start < int(page_bar_num / 2) * 2:
            for i in range(int(page_bar_num / 2) * 2):
                if page_start - 1 >= 1 and page_end - page_start < int(page_bar_num / 2) * 2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end + 1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))
