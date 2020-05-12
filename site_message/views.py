import json

from django.forms import (BooleanField, CharField, ChoiceField, DateTimeField,
                          Form, IntegerField, MultipleChoiceField)
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import localtime, now
from django.views import View

from account.models import User

from .models import Message


class MessageListAPI(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class MessageListAPIGetForm(Form):
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
            box_choices = (
                ("inbox", "inbox"),
                ("outbox", "outbox"),
            )
            box = ChoiceField(choices=box_choices)
        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = MessageListAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            if cleaned_data['offset'] is None:
                cleaned_data['offset'] = 0
            if cleaned_data['limit'] is None:
                cleaned_data['limit'] = 10

            if cleaned_data['box'] == 'inbox':
                result = list(Message.objects.filter(recipient=request.user, is_deleted_by_recipient=False)[
                    cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))

            elif cleaned_data['box'] == 'outbox':
                result = list(Message.objects.filter(sender=request.user, is_deleted_by_sender=False)[
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
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class MessageListAPIPostForm(Form):
            title = CharField(max_length=255)
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
                cleaned_data['recipient'] = User.objects.get(
                    pk=cleaned_data['recipient'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'RecipientNotFound',
                }, status=400)

            message = Message(title=cleaned_data['title'], send_date=now(
            ), sender=request.user, recipient=cleaned_data['recipient'], content=cleaned_data['content'])

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
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

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
            query_data = cleaned_data['column'].copy()
            if not 'sender' in cleaned_data['column']:
                query_data.append('sender')
            if not 'recipient' in cleaned_data['column']:
                query_data.append('recipient')

            try:
                result = list(Message.objects.filter(pk=message_id).values(
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

            if result[0]['sender'] != request.user.id and result[0]['recipient'] != request.user.id:
                return JsonResponse({
                    'status': 403,
                    'message': 'Forbidden'
                }, status=403)

            if not 'sender' in cleaned_data['column']:
                for each in result:
                    del each['sender']

            if not 'recipient' in cleaned_data['column']:
                for each in result:
                    del each['recipient']

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
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        try:
            message = Message.objects.get(pk=message_id)
        except Exception as e:
            return JsonResponse({
                'status': 404,
                'message': 'Not Found',
            }, status=404)

        if message.sender == request.user:
            message.is_deleted_by_sender = True
            message.save()

        elif message.recipient == request.user:
            message.is_deleted_by_recipient = True
            message.save()

        else:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        if message.is_deleted_by_sender and message.is_deleted_by_recipient:
            message.delete()

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })
