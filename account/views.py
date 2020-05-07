from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.forms import Form, ModelForm, CharField, PasswordInput, IntegerField, MultipleChoiceField, BooleanField, DecimalField
from django.db import models
from django.template import loader
from django.core.validators import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timezone import localtime
from django.shortcuts import redirect
from django.urls import reverse
from .models import UserManager, User
from storage.models import BlobStorage
import json


class UserListAPI(View):
    def get(self, request):
        class UserListAPIGetForm(Form):
            id_start = IntegerField(initial=1, required=False)
            id_end = IntegerField(initial=10, required=False)
            choices = (
                ("last_login", "last login"),
                ("is_superuser", "is superuser"),
                ("username", "username"),
                ("name", "name"),
                ("balance", "balance"),
                ("profile", "profile"),
                ("picture_id", "picture id"),
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

            if cleaned_data['id_start'] is None and cleaned_data['id_end'] is not None:
                cleaned_data['id_start'] = cleaned_data['id_end'] - 10
            else:
                cleaned_data['id_start'] = 1
            if cleaned_data['id_end'] is None:
                cleaned_data['id_end'] = cleaned_data['id_start'] + 10

            result = list(User.objects.filter(id__range=[
                          cleaned_data['id_start'], cleaned_data['id_end']]).values('id', *cleaned_data['column']))

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
                ("last_login", "last login"),
                ("is_superuser", "is superuser"),
                ("username", "username"),
                ("name", "name"),
                ("balance", "balance"),
                ("profile", "profile"),
                ("picture_id", "picture id"),
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

            try:
                result = list(User.objects.get(pk=user_id).values(
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
        class UserAPIPutForm(Form):
            username = CharField()
            password = CharField(widget=PasswordInput)
            is_superuser = BooleanField()
            name = CharField()
            balance = DecimalField(
                max_digits=15, decimal_places=2)
            profile = CharField()

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
            if url_has_allowed_host_and_scheme(iri_to_uri(cleaned_data['redirect_uri']), settings.ALLOWED_HOSTS):
                cleaned_data['redirect_uri'] = iri_to_uri(
                    cleaned_data['redirect_uri'])
            else:
                cleaned_data['redirect_uri'] = '/'

            user = authenticate(
                username=cleaned_data['username'], password=cleaned_data['password'])
            if user is not None:
                logout(request)
                login(request, user)
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
