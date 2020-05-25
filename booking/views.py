import json

from django.db import transaction
from django.db.models import Q
from django.forms import (CharField, ChoiceField, DateTimeField, Form,
                          IntegerField, MultipleChoiceField)
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import localtime, now
from django.views import View

from account.models import User
from course.models import Course, CourseInstance
from site_log.models import Log

from .models import Booking


class BookingListAPI(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class BookingListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            start_date = DateTimeField(required=False)
            end_date = DateTimeField(required=False)
            choices = (
                ("course", "course"),
                ("start_date", "start_date"),
                ("end_date", "end_date"),
                ("teacher", "teacher"),
                ("student", "student"),
                ("info", "info"),
            )
            column = MultipleChoiceField(choices=choices)
            panel_choices = (
                ("teacher", "teacher"),
                ("student", "student"),
                ("all", "all"),
            )
            panel = ChoiceField(choices=panel_choices)

        form = BookingListAPIGetForm(request.GET)
        if form.is_valid():
            cleaned_data = form.clean()

            filter_param = {}
            if cleaned_data['start_date'] is not None:
                filter_param['start_date__gte'] = cleaned_data['start_date']
            if cleaned_data['end_date'] is not None:
                filter_param['start_date__lt'] = cleaned_data['end_date']

            result = []
            if cleaned_data['offset'] is not None or cleaned_data['limit'] is not None:
                if cleaned_data['offset'] is None:
                    cleaned_data['offset'] = 0
                if cleaned_data['limit'] is None:
                    cleaned_data['limit'] = 10

                if cleaned_data['panel'] == 'all':
                    if request.user.is_superuser:
                        result = list(Booking.objects.filter(**filter_param)[
                            cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))
                    else:
                        return JsonResponse({
                            'status': 403,
                            'message': 'Forbidden'
                        }, status=403)
                elif cleaned_data['panel'] == 'teacher':
                    if request.user.groups.filter(name='teacher').exists() or request.user.is_superuser:
                        result = list(Booking.objects.filter(**filter_param, teacher=request.user)[
                            cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))
                    else:
                        return JsonResponse({
                            'status': 403,
                            'message': 'Forbidden'
                        }, status=403)
                elif cleaned_data['panel'] == 'student':
                    study_course_instance = CourseInstance.objects.filter(
                        student=request.user, quota__gt=0)
                    study_course = []
                    for each in study_course_instance:
                        study_course.append(each.course)

                    query_data = cleaned_data['column'].copy()
                    if not 'student' in cleaned_data['column']:
                        query_data.append('student')

                    result = list(Booking.objects.filter(**filter_param, course__in=study_course)[
                        cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *query_data))

                    if 'info' in cleaned_data['column']:
                        for each in result:
                            if each['student'] is not None and each['student'] != request.user.id:
                                each['student'] = 0
                                each['info'] = ''
                            if each['student'] is None:
                                each['info'] = ''
                    else:
                        for each in result:
                            if each['student'] is not None and each['student'] != request.user.id:
                                each['student'] = 0
                            if each['student'] is None:
                                each['info'] = ''

                    if not 'student' in cleaned_data['column']:
                        for each in result:
                            del each['student']
            else:
                if cleaned_data['panel'] == 'all':
                    if request.user.is_superuser:
                        result = list(Booking.objects.filter(
                            **filter_param).values('id', *cleaned_data['column']))
                    else:
                        return JsonResponse({
                            'status': 403,
                            'message': 'Forbidden'
                        }, status=403)
                elif cleaned_data['panel'] == 'teacher':
                    if request.user.groups.filter(name='teacher').exists() or request.user.is_superuser:
                        result = list(Booking.objects.filter(
                            **filter_param, teacher=request.user).values('id', *cleaned_data['column']))
                    else:
                        return JsonResponse({
                            'status': 403,
                            'message': 'Forbidden'
                        }, status=403)
                elif cleaned_data['panel'] == 'student':
                    study_course_instance = CourseInstance.objects.filter(
                        student=request.user, quota__gt=0)
                    study_course = []
                    for each in study_course_instance:
                        study_course.append(each.course)

                    query_data = cleaned_data['column'].copy()
                    if not 'student' in cleaned_data['column']:
                        query_data.append('student')

                    result = list(Booking.objects.filter(
                        **filter_param, course__in=study_course).values('id', *query_data))

                    if 'info' in cleaned_data['column']:
                        for each in result:
                            if each['student'] is not None and each['student'] != request.user.id:
                                each['student'] = 0
                                each['info'] = ''
                            if each['student'] is None:
                                each['info'] = ''
                    else:
                        for each in result:
                            if each['student'] is not None and each['student'] != request.user.id:
                                each['student'] = 0
                            if each['student'] is None:
                                each['info'] = ''

                    if not 'student' in cleaned_data['column']:
                        for each in result:
                            del each['student']

            if 'date' in cleaned_data['column']:
                for each in result:
                    each['date'] = localtime(each['date'])

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

        class BookingListAPIPostForm(Form):
            course = IntegerField()
            start_date = DateTimeField()
            end_date = DateTimeField()
            teacher = CharField(required=False)
            info = CharField(required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = BookingListAPIPostForm(data)
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

            if request.user.is_superuser:
                if 'teacher' in data and cleaned_data['teacher'] is not None and cleaned_data['teacher'] != '':
                    try:
                        cleaned_data['teacher'] = User.objects.get(
                            username=cleaned_data['teacher'])
                    except Exception as e:
                        return JsonResponse({
                            'status': 400,
                            'message': 'TeacherNotFound',
                        }, status=400)
                else:
                    cleaned_data['teacher'] = cleaned_data['course'].teacher
            else:
                cleaned_data['teacher'] = request.user

            if cleaned_data['course'].teacher != request.user and not request.user.is_superuser:
                return JsonResponse({
                    'status': 403,
                    'message': 'Forbidden'
                }, status=403)

            if (cleaned_data['start_date'] > cleaned_data['end_date']) or (cleaned_data['start_date'] < cleaned_data['course'].start_date) or (cleaned_data['end_date'] > cleaned_data['course'].end_date):
                return JsonResponse({
                    'status': 400,
                    'message': 'InvalidDate',
                }, status=400)

            crash_booking = Booking.objects.filter(Q(start_date__gt=cleaned_data['start_date'], start_date__lt=cleaned_data['end_date'], teacher=cleaned_data['teacher']) | Q(
                end_date__gt=cleaned_data['start_date'], end_date__lt=cleaned_data['end_date'], teacher=cleaned_data['teacher']))

            if crash_booking:
                return JsonResponse({
                    'status': 400,
                    'message': 'TimeCrash',
                }, status=400)

            booking = Booking(course=cleaned_data['course'], start_date=cleaned_data['start_date'],
                              end_date=cleaned_data['end_date'], teacher=cleaned_data['teacher'], info=cleaned_data['info'])
            try:
                with transaction.atomic():
                    booking.save()
                    log = Log(user=request.user, date=now(
                    ), operation='Create a booking for course ' + cleaned_data['course'].name + '(booking id:' + str(booking.id) + ')')
                    log.save()
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


class BookingAPI(View):
    def get(self, request, booking_id):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class BookingAPIGetForm(Form):
            choices = (
                ("course", "course"),
                ("start_date", "start_date"),
                ("end_date", "end_date"),
                ("teacher", "teacher"),
                ("student", "student"),
                ("info", "info"),
            )
            column = MultipleChoiceField(choices=choices)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = BookingAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()
            query_data = cleaned_data['column'].copy()
            if not 'student' in cleaned_data['column']:
                query_data.append('student')
            if not 'teacher' in cleaned_data['column']:
                query_data.append('teacher')
            if not 'course' in cleaned_data['column']:
                query_data.append('course')

            try:
                result = list(Booking.objects.filter(pk=booking_id).values(
                    'id', *query_data))
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

            if result[0]['teacher'] == request.user.id or request.user.is_superuser:
                pass
            else:
                if CourseInstance.objects.filter(course=result[0]['course'], student=request.user, quota__gt=0).exists():
                    pass
                elif CourseInstance.objects.filter(course=result[0]['course'], student=request.user, quota=0).exists():
                    if result[0]['student'] is not None and result[0]['student'] != request.user.id:
                        return JsonResponse({
                            'status': 403,
                            'message': 'Forbidden'
                        }, status=403)
                    else:
                        pass
                else:
                    return JsonResponse({
                        'status': 403,
                        'message': 'Forbidden'
                    }, status=403)

                if result[0]['student'] is not None and result[0]['student'] != request.user.id:
                    result[0]['student'] = 0
                    if 'info' in cleaned_data['column']:
                        result[0]['info'] = ''
                if result[0]['student'] is None:
                    if 'info' in cleaned_data['column']:
                        result[0]['info']

            if not 'student' in cleaned_data['column']:
                del result[0]['student']
            if not 'teacher' in cleaned_data['column']:
                del result[0]['teacher']
            if not 'course' in cleaned_data['column']:
                del result[0]['course']

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

    def patch(self, request, booking_id):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class BookingAPIPatchForm(Form):
            start_date = DateTimeField(required=False)
            end_date = DateTimeField(required=False)
            student = CharField(required=False)
            info = CharField(required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = BookingAPIPatchForm(data)
        if form.is_valid():
            try:
                booking = Booking.objects.get(
                    pk=booking_id)
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            if booking.teacher == request.user or request.user.is_superuser:
                pass
            else:
                if CourseInstance.objects.filter(course=booking.course, student=request.user, quota__gt=0).exists():
                    pass
                else:
                    return JsonResponse({
                        'status': 403,
                        'message': 'Forbidden'
                    }, status=403)

            cleaned_data = form.clean()

            if booking.teacher == request.user or request.user.is_superuser:
                if (cleaned_data['start_date'] is not None and booking.start_date != cleaned_data['start_date']) or (cleaned_data['end_date'] is not None and booking.end_date != cleaned_data['end_date']):
                    if booking.student is not None and cleaned_data['student'] is not None and cleaned_data['student'] != '':
                        return JsonResponse({
                            'status': 400,
                            'message': 'StudentAlreadyBookedIt',
                        }, status=400)
                    else:
                        if cleaned_data['start_date'] is None:
                            cleaned_data['start_date'] = booking.start_date
                        if cleaned_data['end_date'] is None:
                            cleaned_data['end_date'] = booking.end_date

                        if (cleaned_data['start_date'] > cleaned_data['end_date']) or (cleaned_data['start_date'] < booking.course.start_date) or (cleaned_data['end_date'] > booking.course.end_date):
                            return JsonResponse({
                                'status': 400,
                                'message': 'InvalidDate',
                            }, status=400)

                        crash_booking = Booking.objects.filter(Q(start_date__gt=cleaned_data['start_date'], start_date__lt=cleaned_data['end_date'], teacher=booking.teacher) | Q(
                            end_date__gt=cleaned_data['start_date'], end_date__lt=cleaned_data['end_date'], teacher=booking.teacher))

                        if crash_booking:
                            for each in crash_booking:
                                if each != booking:
                                    return JsonResponse({
                                        'status': 400,
                                        'message': 'TimeCrash',
                                    }, status=400)

                        if cleaned_data['start_date'] is not None:
                            booking.start_date = cleaned_data['start_date']

                        if cleaned_data['end_date'] is not None:
                            booking.end_date = cleaned_data['end_date']

                        try:
                            with transaction.atomic():
                                booking.save()
                                log = Log(user=request.user, date=now(
                                ), operation='Update a booking\'s date (course:' + booking.course.name + ' booking id:' + str(booking.id) + ')')
                                log.save()
                        except Exception as e:
                            return JsonResponse({
                                'status': 500,
                                'message': 'DatabaseError',
                            }, status=500)

                if cleaned_data['student'] is not None:
                    if cleaned_data['student'] != '':
                        if booking.student is None or cleaned_data['student'] != booking.student.username:
                            try:
                                cleaned_data['student'] = User.objects.get(
                                    username=cleaned_data['student'])
                            except Exception as e:
                                return JsonResponse({
                                    'status': 400,
                                    'message': 'StudentNotFound',
                                }, status=400)

                            course_instance = CourseInstance.objects.filter(
                                course=booking.course, student=cleaned_data['student'], quota__gt=0)
                            if not course_instance.exists():
                                return JsonResponse({
                                    'status': 400,
                                    'message': 'InsufficientQuota',
                                }, status=400)

                            crash_booking = Booking.objects.filter(Q(start_date__gt=booking.start_date, start_date__lt=booking.end_date, student=request.user) | Q(
                                end_date__gt=booking.start_date, end_date__lt=booking.end_date, student=request.user))

                            if crash_booking:
                                for each in crash_booking:
                                    if each != booking:
                                        return JsonResponse({
                                            'status': 400,
                                            'message': 'TimeCrash',
                                        }, status=400)

                            if booking.start_date > now():
                                course_instance_target = course_instance[0]
                                try:
                                    with transaction.atomic():
                                        booking.student = cleaned_data['student']
                                        course_instance_target.quota = course_instance_target.quota - 1
                                        log = Log(user=request.user, date=now(), operation='Update a booking\'s student (course:' +
                                                  booking.course.name + ' booking id:' + str(booking.id) + ' student id:' + str(cleaned_data['student'].id) + ')')
                                        log.save()
                                        booking.save()
                                        course_instance_target.save()
                                except Exception as e:
                                    return JsonResponse({
                                        'status': 500,
                                        'message': 'DatabaseError',
                                    }, status=500)
                            else:
                                return JsonResponse({
                                    'status': 400,
                                    'message': 'AlreadyGone',
                                }, status=400)
                    else:
                        if booking.student is not None:
                            if booking.start_date > now():
                                course_instance = CourseInstance.objects.filter(
                                    course=booking.course, student=booking.student)

                                course_instance_target = course_instance[0]
                                try:
                                    with transaction.atomic():
                                        log = Log(user=request.user, date=now(), operation='Cancel a booking (course:' +
                                                  booking.course.name + ' booking id:' + str(booking.id) + ' student id:' + str(booking.student.id) + ')')
                                        log.save()
                                        booking.student = None
                                        course_instance_target.quota = course_instance_target.quota + 1
                                        booking.save()
                                        course_instance_target.save()
                                except Exception as e:
                                    return JsonResponse({
                                        'status': 500,
                                        'message': 'DatabaseError',
                                    }, status=500)
                            else:
                                return JsonResponse({
                                    'status': 400,
                                    'message': 'AlreadyGone',
                                }, status=400)

                if 'info' in data:
                    try:
                        with transaction.atomic():
                            booking.info = cleaned_data['info']
                            log = Log(user=request.user, date=now(), operation='Update a booking\'s info (course:' +
                                      booking.course.name + ' booking id:' + str(booking.id) + ')')
                            log.save()
                            booking.save()
                    except Exception as e:
                        return JsonResponse({
                            'status': 500,
                            'message': 'DatabaseError',
                        }, status=500)
            else:
                if cleaned_data['student'] == request.user.username and booking.student is None:
                    course_instance = CourseInstance.objects.filter(
                        course=booking.course, student=request.user, quota__gt=0)
                    if not course_instance.exists():
                        return JsonResponse({
                            'status': 400,
                            'message': 'InsufficientQuota',
                        }, status=400)

                    crash_booking = Booking.objects.filter(Q(start_date__gt=booking.start_date, start_date__lt=booking.end_date, student=request.user) | Q(
                        end_date__gt=booking.start_date, end_date__lt=booking.end_date, student=request.user))

                    if crash_booking:
                        for each in crash_booking:
                            if each != booking:
                                return JsonResponse({
                                    'status': 400,
                                    'message': 'TimeCrash',
                                }, status=400)

                    if booking.start_date > now():
                        course_instance_target = course_instance[0]
                        try:
                            with transaction.atomic():
                                booking.student = request.user
                                course_instance_target.quota = course_instance_target.quota - 1
                                booking.save()
                                course_instance_target.save()
                                log = Log(user=request.user, date=now(), operation='Update a booking\'s student (course:' +
                                          booking.course.name + ' booking id:' + str(booking.id) + ' student id:' + str(request.user.id) + ')')
                                log.save()
                        except Exception as e:
                            return JsonResponse({
                                'status': 500,
                                'message': 'DatabaseError',
                            }, status=500)
                    else:
                        return JsonResponse({
                            'status': 400,
                            'message': 'AlreadyGone',
                        }, status=400)
                elif booking.student == request.user and cleaned_data['student'] is not None and cleaned_data['student'] == '':
                    if booking.start_date > now():
                        try:
                            with transaction.atomic():
                                log = Log(user=request.user, date=now(), operation='Cancel a booking (course:' +
                                          booking.course.name + ' booking id:' + str(booking.id) + ' student id:' + str(booking.student.id) + ')')
                                log.save()
                                course_instance = CourseInstance.objects.filter(
                                    course=booking.course, student=request.user)
                                course_instance_target = course_instance[0]
                                course_instance_target.quota = course_instance_target.quota + 1
                                booking.student = None

                                course_instance_target.save()
                                booking.save()
                        except Exception as e:
                            return JsonResponse({
                                'status': 500,
                                'message': 'DatabaseError',
                            }, status=500)
                    else:
                        return JsonResponse({
                            'status': 400,
                            'message': 'AlreadyGone',
                        }, status=400)
                elif booking.student == request.user and (cleaned_data['student'] is None or cleaned_data['student'] == request.user.username):
                    pass
                else:
                    return JsonResponse({
                        'status': 403,
                        'message': 'Forbidden'
                    }, status=403)

            return JsonResponse({
                'status': 200,
                'message': 'Success',
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def delete(self, request, booking_id):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        try:
            booking = Booking.objects.get(pk=booking_id)
        except Exception as e:
            return JsonResponse({
                'status': 404,
                'message': 'Not Found',
            }, status=404)

        if booking.student == request.user:
            if booking.start_date > now():
                try:
                    with transaction.atomic():
                        log = Log(user=request.user, date=now(), operation='Cancel a booking (course:' +
                                  booking.course.name + ' booking id:' + str(booking.id) + ' student id:' + str(booking.student.id) + ')')
                        log.save()
                        course_instance = CourseInstance.objects.filter(
                            course=booking.course, student=request.user)
                        course_instance_target = course_instance[0]
                        course_instance_target.quota = course_instance_target.quota + 1
                        booking.student = None

                        course_instance_target.save()
                        booking.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)

        elif booking.teacher == request.user or request.user.is_superuser:
            if booking.student is not None:
                if booking.start_date > now():
                    try:
                        with transaction.atomic():
                            log = Log(user=request.user, date=now(), operation='Cancel a booking (course:' +
                                      booking.course.name + ' booking id:' + str(booking.id) + ' student id:' + str(booking.student.id) + ')')
                            log.save()
                            course_instance = CourseInstance.objects.filter(
                                course=booking.course, student=booking.student)
                            course_instance_target = course_instance[0]
                            course_instance_target.quota = course_instance_target.quota + 1
                            booking.student = None

                            course_instance_target.save()
                            booking.save()
                    except Exception as e:
                        return JsonResponse({
                            'status': 500,
                            'message': 'DatabaseError',
                        }, status=500)
            try:
                with transaction.atomic():
                    log = Log(user=request.user, date=now(), operation='Delete a booking (course:' +
                              booking.course.name + ' booking id:' + str(booking.id) + ')')
                    log.save()
                    booking.delete()
            except Exception as e:
                return JsonResponse({
                    'status': 500,
                    'message': 'DatabaseError',
                }, status=500)
        else:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })
