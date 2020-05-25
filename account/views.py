import base64
import json

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.core.validators import ValidationError
from django.db import models, transaction
from django.forms import (BooleanField, CharField, DecimalField, FileField,
                          Form, IntegerField, MultipleChoiceField,
                          PasswordInput)
from django.http import HttpResponse, JsonResponse, QueryDict
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse
from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timezone import localtime, now
from django.views import View

from account.models import User
from finance.models import Bill
from site_log.models import Log
from storage.models import BlobStorage

from .models import User, UserManager


class UserListAPI(View):
    def get(self, request):
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class UserListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("last_login", "last_login"),
                ("is_superuser", "is_superuser"),
                ("username", "username"),
                ("name", "name"),
                ("balance", "balance"),
                ("profile", "profile"),
                ("picture_id", "picture_id"),
            )
            column = MultipleChoiceField(choices=choices)

        form = UserListAPIGetForm(request.GET)
        if form.is_valid():
            cleaned_data = form.clean()

            if cleaned_data['offset'] is None:
                cleaned_data['offset'] = 0
            if cleaned_data['limit'] is None:
                cleaned_data['limit'] = 10

            result = list(User.objects.all()[
                          cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))

            if 'last_login' in cleaned_data['column']:
                for each in result:
                    each['last_login'] = localtime(each['last_login'])

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
        class UserListAPIPostForm(Form):
            username = CharField()
            password = CharField(widget=PasswordInput)
            name = CharField()
            role = CharField(required=False)
            balance = DecimalField(
                max_digits=15, decimal_places=2, required=False)
            profile = CharField(required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = UserListAPIPostForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            if User.objects.filter(username=cleaned_data['username']).exists():
                return JsonResponse({
                    'status': 409,
                    'message': 'UserAlreadyExisted'
                }, status=409)

            user_manager = UserManager()
            user = user_manager.create_user(
                cleaned_data['username'], cleaned_data['password'], cleaned_data['name'])

            if request.user.is_superuser and (cleaned_data['role'] == 'admin' or cleaned_data['role'] == 'teacher' or cleaned_data['role'] == 'student'):
                teacher_group = Group.objects.get(name='teacher')
                if cleaned_data['role'] == 'admin':
                    user.is_superuser = True
                    user.groups.add(teacher_group)
                else:
                    user.is_superuser = False

                if cleaned_data['role'] == 'teacher':
                    user.groups.add(teacher_group)
                else:
                    user.groups.remove(teacher_group)

            if cleaned_data['profile'] != '':
                user.profile = cleaned_data['profile']

            if request.user is None:
                try:
                    with transaction.atomic():
                        user.save()
                        log = Log(user=user, date=now(), operation='Sign up')
                        log.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)
            else:
                try:
                    with transaction.atomic():
                        user.save()
                        log = Log(user=user, date=now(), operation='Add by an administrator ' + request.user.username)
                        log.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)

            if request.user.is_superuser and cleaned_data['balance'] is not None:
                try:
                    with transaction.atomic():
                        bill = Bill(user=user, amount=cleaned_data['balance'], date=now(
                        ), info='Adjust the balance by an administrator ' + request.user.username)
                        user.balance = user.balance + cleaned_data['balance']

                        bill.save()
                        user.save()
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


class UserAPI(View):
    def get(self, request, user_id):
        class UserAPIGetForm(Form):
            choices = (
                ("last_login", "last_login"),
                ("is_superuser", "is_superuser"),
                ("username", "username"),
                ("name", "name"),
                ("balance", "balance"),
                ("profile", "profile"),
                ("picture_id", "picture_id"),
            )
            column = MultipleChoiceField(choices=choices)

        form = UserAPIGetForm(request.GET)
        if form.is_valid():
            cleaned_data = form.clean()
            if 'balance' in cleaned_data['column']:
                if not request.user.is_superuser and request.user.id != user_id:
                    cleaned_data['column'].remove('balance')

            try:
                result = list(User.objects.filter(pk=user_id).values(
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

            if 'last_login' in cleaned_data['column']:
                for each in result:
                    each['last_login'] = localtime(each['last_login'])

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

    def put(self, request, user_id):
        if not request.user.is_superuser and request.user.id != user_id:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class UserAPIPutForm(Form):
            username = CharField()
            password = CharField(widget=PasswordInput)
            role = CharField()
            name = CharField()
            balance = DecimalField(
                max_digits=15, decimal_places=2)
            profile = CharField(required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = UserAPIPutForm(data)
        if form.is_valid():
            try:
                user = User.objects.get(pk=user_id)
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            cleaned_data = form.clean()
            user_manager = UserManager()

            if cleaned_data['username'] != '' and user.username != cleaned_data['username']:
                if not User.objects.filter(username=cleaned_data['username']).exists():
                    user.username == cleaned_data['username']

            if cleaned_data['password'] != '':
                user.set_password(cleaned_data['password'])

            if cleaned_data['name'] != '':
                user.name = cleaned_data['name']

            if request.user.is_superuser and (cleaned_data['role'] == 'admin' or cleaned_data['role'] == 'teacher' or cleaned_data['role'] == 'student'):
                teacher_group = Group.objects.get(name='teacher')
                if cleaned_data['role'] == 'admin':
                    user.is_superuser = True
                    user.groups.add(teacher_group)
                else:
                    user.is_superuser = False

                if cleaned_data['role'] == 'teacher':
                    user.groups.add(teacher_group)
                else:
                    user.groups.remove(teacher_group)

            if cleaned_data['profile'] != '':
                user.profile = cleaned_data['profile']

            if request.user.id == user.id:
                try:
                    with transaction.atomic():
                        user.save()
                        log = Log(user=user, date=now(), operation='Update profile')
                        log.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)
            else:
                try:
                    with transaction.atomic():
                        user.save()
                        log = Log(user=user, date=now(), operation='Update profile by an administrator ' + request.user.username)
                        log.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)

            if request.user.is_superuser and cleaned_data['balance'] is not None:
                balance_diff = cleaned_data['balance'] - user.balance
                try:
                    with transaction.atomic():
                        bill = Bill(user=user, amount=balance_diff, date=now(
                        ), info='Adjust the balance by an administrator ' + request.user.username)
                        user.balance = user.balance + balance_diff

                        bill.save()
                        user.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)

            return JsonResponse({
                'status': 200,
                'message': 'Success',
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def post(self, request, user_id):
        if not request.user.is_superuser and request.user.id != user_id:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class UserAPIPostForm(Form):
            username = CharField(required=False)
            password = CharField(widget=PasswordInput, required=False)
            name = CharField(required=False)
            role = CharField(required=False)
            balance = DecimalField(
                max_digits=15, decimal_places=2, required=False)
            profile = CharField(required=False)
            picture = FileField(required=False)

        form = UserAPIPostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = User.objects.get(pk=user_id)
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            cleaned_data = form.clean()
            user_manager = UserManager()

            if cleaned_data['username'] != '' and user.username != cleaned_data['username']:
                if not User.objects.filter(username=cleaned_data['username']).exists():
                    user.username = cleaned_data['username']

            if cleaned_data['password'] != '':
                user.set_password(cleaned_data['password'])

            if cleaned_data['name'] != '':
                user.name = cleaned_data['name']

            if request.user.is_superuser and (cleaned_data['role'] == 'admin' or cleaned_data['role'] == 'teacher' or cleaned_data['role'] == 'student'):
                teacher_group = Group.objects.get(name='teacher')
                if cleaned_data['role'] == 'admin':
                    user.is_superuser = True
                    user.groups.add(teacher_group)
                else:
                    user.is_superuser = False

                if cleaned_data['role'] == 'teacher':
                    user.groups.add(teacher_group)
                else:
                    user.groups.remove(teacher_group)

            if cleaned_data['profile'] != '':
                user.profile = cleaned_data['profile']

            if cleaned_data['picture'] is not None:
                if cleaned_data['picture'].content_type[:5] != 'image':
                    return JsonResponse({
                        'status': 400,
                        'message': 'IllegalFileType'
                    }, status=400)
                if user.picture is None:
                    try:
                        with transaction.atomic():
                            blob_storage = BlobStorage(data=cleaned_data['picture'].file.read(
                            ), content_type=cleaned_data['picture'].content_type)
                            blob_storage.save()
                            user.picture = blob_storage
                            user.save()
                    except Exception as e:
                        return JsonResponse({
                            'status': 500,
                            'message': 'DatabaseError',
                        }, status=500)
                else:
                    try:
                        with transaction.atomic():
                            user.picture.data = data = cleaned_data['picture'].file.read(
                            )
                            user.picture.content_type = cleaned_data['picture'].content_type
                            user.picture.save()
                            user.save()
                    except Exception as e:
                        return JsonResponse({
                            'status': 500,
                            'message': 'DatabaseError',
                        }, status=500)

            if request.user.id == user.id:
                try:
                    with transaction.atomic():
                        user.save()
                        log = Log(user=user, date=now(), operation='Update profile')
                        log.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)
            else:
                try:
                    with transaction.atomic():
                        user.save()
                        log = Log(user=user, date=now(), operation='Update profile by an administrator ' + request.user.username)
                        log.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)

            if request.user.is_superuser and cleaned_data['balance'] is not None:
                balance_diff = cleaned_data['balance'] - user.balance
                try:
                    with transaction.atomic():
                        bill = Bill(user=user, amount=balance_diff, date=now(
                        ), info='Adjust the balance by an administrator ' + request.user.username)
                        user.balance = user.balance + balance_diff

                        bill.save()
                        user.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)

            return JsonResponse({
                'status': 200,
                'message': 'Success',
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def delete(self, request, user_id):
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        try:
            user = User.objects.get(pk=user_id)
        except Exception as e:
            return JsonResponse({
                'status': 404,
                'message': 'Not Found',
            }, status=404)

        try:
            with transaction.atomic():
                if user.picture is not None:
                    user.picture.delete()
                log = Log(user=request.user, date=now(), operation='Delete a user ' + user.username + '(id:' + user.id + ')')
                log.save()
                user.delete()
        except Exception as e:
            return JsonResponse({
                'status': 500,
                'message': 'DatabaseError',
            }, status=500)

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })


class UserLoginAPI(View):
    def get(self, request):
        if request.user.is_authenticated:
            return JsonResponse({
                'status': 200,
                'message': 'Success',
                'data': {
                    'is_authenticated': True,
                    'username': request.user.username,
                },
            })
        else:
            return JsonResponse({
                'status': 200,
                'message': 'Success',
                'data': {
                    'is_authenticated': False,
                },
            })

    def post(self, request):
        class UserLoginForm(Form):
            username = CharField()
            password = CharField(widget=PasswordInput)
            redirect_uri = CharField(required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = UserLoginForm(data)
        if form.is_valid():
            cleaned_data = form.clean()
            if 'redirect_uri' in data and cleaned_data['redirect_uri'] != url_has_allowed_host_and_scheme(iri_to_uri(cleaned_data['redirect_uri']), settings.ALLOWED_HOSTS):
                cleaned_data['redirect_uri'] = iri_to_uri(
                    cleaned_data['redirect_uri'])
            else:
                cleaned_data['redirect_uri'] = '/'

            user = authenticate(
                username=cleaned_data['username'], password=cleaned_data['password'])
            if user is not None:
                logout(request)
                login(request, user)
                request.session['is_teacher'] = request.user.groups.filter(
                    name='teacher').exists()
                try:
                    with transaction.atomic():
                        log = Log(user=request.user, date=now(), operation='Login')
                        log.save()
                except Exception as e:
                    return JsonResponse({
                        'status': 500,
                        'message': 'DatabaseError',
                    }, status=500)
                return JsonResponse({
                    'status': 200,
                    'message': 'Success',
                    'redirect_uri': cleaned_data['redirect_uri'],
                })
            else:
                return JsonResponse({
                    'status': 403,
                    'message': 'Login failed'
                }, status=403)
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)


class UserLogoutAPI(View):

    def post(self, request):

        try:
            logout(request)
            request.session.flush()

        except:
            return JsonResponse({
                'status': 500,
                'message': 'InternalServerError'
            }, status=500)

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })


class UserSignupView(View):

    def get(self, request):
        if request.user.is_authenticated:
            if url_has_allowed_host_and_scheme(iri_to_uri(request.GET.get('redirect_uri', default='/')), settings.ALLOWED_HOSTS):
                return redirect(iri_to_uri(request.GET.get('redirect_uri', default='/')))
            else:
                return redirect(reverse('home'))

        template = loader.get_template('account/signup.html')
        context = {}
        context['site_name'] = settings.SITE_NAME
        context['hide_signup'] = True
        return HttpResponse(template.render(context, request))


class UserLoginView(View):

    def get(self, request):
        if request.user.is_authenticated:
            if url_has_allowed_host_and_scheme(iri_to_uri(request.GET.get('redirect_uri', default='/')), settings.ALLOWED_HOSTS):
                return redirect(iri_to_uri(request.GET.get('redirect_uri', default='/')))
            else:
                return redirect(reverse('home'))

        template = loader.get_template('account/login.html')
        context = {}
        context['site_name'] = settings.SITE_NAME
        context['hide_login'] = True
        return HttpResponse(template.render(context, request))


class UserProfileView(View):

    def get(self, request, user_id):

        template = loader.get_template('account/profile.html')

        context = {}
        try:
            user = User.objects.get(pk=user_id)
            context['status'] = 200
            context['user'] = user
            if user.is_superuser:
                context['role'] = 'Admin'
            elif user.groups.filter(name='teacher').exists():
                context['role'] = 'Teacher'
            else:
                context['role'] = 'Student'
        except Exception as e:
            context['status'] = 404

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        if user.picture is not None:
            context['picture'] = 'data:' + user.picture.content_type + \
                ';base64,' + \
                str(base64.b64encode(user.picture.data), encoding='utf-8')

        return HttpResponse(template.render(context, request))
