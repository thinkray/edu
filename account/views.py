import json

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.validators import ValidationError
from django.db import models
from django.forms import (BooleanField, CharField, DecimalField, Form,
                          IntegerField, ModelForm, MultipleChoiceField,
                          PasswordInput)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse
from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timezone import localtime
from django.views import View

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

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = UserListAPIGetForm(data)
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
        class UserListAPIPostForm(ModelForm):
            class Meta:
                model = User
                fields = ['username', 'password', 'name']

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

            user_manager = UserManager()
            user_manager.create_user(
                cleaned_data['username'], cleaned_data['password'], cleaned_data['name'])
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

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = UserAPIGetForm(data)
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
            is_superuser = BooleanField()
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

            if cleaned_data['username'] != '':
                user.username = cleaned_data['username']

            if cleaned_data['password'] != '':
                user.set_password(cleaned_data['password'])

            if 'is_superuser' in data and cleaned_data['is_superuser'] != '':
                user.is_superuser = cleaned_data['is_superuser']

            if cleaned_data['name'] != '':
                user.name = cleaned_data['name']

            if cleaned_data['balance'] is not None:
                user.balance = cleaned_data['balance']

            if cleaned_data['profile'] != '':
                user.profile = cleaned_data['profile']

            user.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success',
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def patch(self, request, user_id):
        if not request.user.is_superuser and request.user.id != user_id:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class UserAPIPatchForm(Form):
            username = CharField(required=False)
            password = CharField(widget=PasswordInput, required=False)
            is_superuser = BooleanField(required=False)
            name = CharField(required=False)
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

        form = UserAPIPatchForm(data)
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

            if cleaned_data['username'] != '':
                user.username = cleaned_data['username']

            if cleaned_data['password'] != '':
                user.set_password(cleaned_data['password'])

            if 'is_superuser' in data and cleaned_data['is_superuser'] != '':
                user.is_superuser = cleaned_data['is_superuser']

            if cleaned_data['name'] != '':
                user.name = cleaned_data['name']

            if cleaned_data['balance'] is not None:
                user.balance = cleaned_data['balance']

            if cleaned_data['profile'] != '':
                user.profile = cleaned_data['profile']

            user.save()
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

        user.delete()

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
                request.session['is_teacher'] = request.user.groups.filter(name='teacher').exists()
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
