from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.forms import Form, ModelForm, CharField, PasswordInput
from django.db import models
from django.template import loader
from django.core.validators import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme
from .models import UserManager, User
import json


class UserListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

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
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def put(self, request, user_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def patch(self, request, user_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def delete(self, request, user_id):
        return JsonResponse({
            'error': 'NotImplementedError'
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
            redirect_uri = CharField(initial='/', required=False)

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
                cleaned_data['redirect_uri'] = iri_to_uri(cleaned_data['redirect_uri'])
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
        template = loader.get_template('account/signup.html')
        context = {}
        context['site_name'] = settings.SITE_NAME
        return HttpResponse(template.render(context, request))

class UserLoginView(View):

    def get(self, request):
        template = loader.get_template('account/login.html')
        context = {}
        context['site_name'] = settings.SITE_NAME
        return HttpResponse(template.render(context, request))
