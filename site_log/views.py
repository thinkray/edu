import json

from django.db import transaction
from django.forms import CharField, Form, IntegerField, MultipleChoiceField
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import localtime, now
from django.views import View

from account.models import User

from .models import Log


class LogListAPI(View):
    def get(self, request):
        # Initialization form
        class LogListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("user", "user"),
                ("date", "date"),
                ("operation", "operation"),
            )
            column = MultipleChoiceField(choices=choices)

        form = LogListAPIGetForm(request.GET)
        if form.is_valid():
            # Prepare result
            cleaned_data = form.clean()

            if cleaned_data['offset'] is None:
                cleaned_data['offset'] = 0
            if cleaned_data['limit'] is None:
                cleaned_data['limit'] = 10

            if request.user.is_superuser:
                result = list(Log.objects.all()[
                              cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))
            else:
                result = list(Log.objects.filter(user=request.user)[
                              cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))

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
        # Check permission
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden',
            }, status=403)

        # Initialization form
        class LogListAPIPostForm(Form):
            username = CharField()
            operation = CharField()

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = LogListAPIPostForm(data)
        if form.is_valid():
            # Update information
            cleaned_data = form.clean()

            try:
                cleaned_data['username'] = User.objects.get(
                    username=cleaned_data['username'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'UserNotFound',
                }, status=400)

            try:
                with transaction.atomic():
                    log = Log(user=cleaned_data['username'], date=now(
                    ), operation=cleaned_data['operation'])

                    log.save()

                    log_creater = Log(user=request.user, date=now(
                    ), operation='Create a log (id:' + str(log.id) + ')')
                    
                    log_creater.save()
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


class LogAPI(View):
    def get(self, request, log_id):
        # Initialization form
        class LogAPIGetForm(Form):
            choices = (
                ("user", "user"),
                ("date", "date"),
                ("operation", "operation"),
            )
            column = MultipleChoiceField(choices=choices)

        form = LogAPIGetForm(request.GET)
        if form.is_valid():
            # Prepare result
            cleaned_data = form.clean()

            try:
                result = list(Log.objects.filter(pk=log_id).values(
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

            if not request.user.is_superuser and result[0]['user'] != request.user.id:
                return JsonResponse({
                    'status': 403,
                    'message': 'Forbidden',
                    'data': [],
                }, status=403)

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
