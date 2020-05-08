import json

from django.forms import (BooleanField, CharField, DateTimeField, Form,
                          IntegerField, MultipleChoiceField)
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import localtime, now
from django.views import View

from account.models import User

from .models import Message


class MessageListAPI(View):
    def get(self, request):
        class CourseListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("title", "title"),
                ("send_date", "send_date"),
                ("sender", "sender"),
                ("recipient", "recipient"),
                ("content", "content"),
                ("is_unread", "is_unread"),
                ("is_deleted_by_sender", "is_deleted_by_sender"),
                ("is_deleted_by_recipient", "is_deleted_by_recipient"),
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

            result = list(Message.objects.all()[
                          cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))

            if 'send_date' in cleaned_data['column']:
                for each in result:
                    each['send_date'] = localtime(each['send_date'])

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
        class MessageListAPIPostForm(Form):
            title = CharField(max_length=255)
            sender = IntegerField()
            recipient = IntegerField()
            content = CharField()

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = MessageListAPIPostForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                cleaned_data['sender'] = User.objects.get(
                    pk=cleaned_data['sender'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'SenderNotFound',
                }, status=400)

            try:
                cleaned_data['recipient'] = User.objects.get(
                    pk=cleaned_data['recipient'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'RecipientNotFound',
                }, status=400)

            message = Message(title=cleaned_data['title'], send_date=now(
            ), sender=cleaned_data['sender'], recipient=cleaned_data['recipient'], content=cleaned_data['content'])

            message.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success'
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)


class MessageAPI(View):
    def get(self, request, message_id):
        class MessageAPIGetForm(Form):
            choices = (
                ("title", "title"),
                ("send_date", "send_date"),
                ("sender", "sender"),
                ("recipient", "recipient"),
                ("content", "content"),
                ("is_unread", "is_unread"),
                ("is_deleted_by_sender", "is_deleted_by_sender"),
                ("is_deleted_by_recipient", "is_deleted_by_recipient"),
            )
            column = MultipleChoiceField(choices=choices)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = MessageAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                result = list(Message.objects.filter(pk=message_id).values(
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

            if 'send_date' in cleaned_data['column']:
                for each in result:
                    each['send_date'] = localtime(each['send_date'])

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

    def delete(self, request, message_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })
