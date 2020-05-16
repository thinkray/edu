import json
from datetime import datetime

from django.conf import settings
from django.core.paginator import Paginator
from django.forms import (BooleanField, CharField, ChoiceField, DateTimeField,
                          Form, IntegerField, MultipleChoiceField)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse
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

            result = []
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
            recipient = CharField()
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
                    username=cleaned_data['recipient'])
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


class MessageCountAPI(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class MessageCountAPIPostForm(Form):
            choices = (
                ("unread", "unread"),
                ("inbox", "inbox"),
                ("outbox", "outbox"),
            )
            target = ChoiceField(choices=choices)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = MessageCountAPIPostForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            count = 0
            if cleaned_data['target'] == 'unread':
                count = Message.objects.filter(
                    recipient=request.user, is_unread=True).count()

            elif cleaned_data['target'] == 'inbox':
                count = Message.objects.filter(recipient=request.user).count()

            elif cleaned_data['target'] == 'outbox':
                count = Message.objects.filter(sender=request.user).count()

            return JsonResponse({
                'status': 200,
                'message': 'Success',
                'count': count,
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
            if not 'is_deleted_by_sender' in cleaned_data['column']:
                query_data.append('is_deleted_by_sender')
            if not 'is_deleted_by_recipient' in cleaned_data['column']:
                query_data.append('is_deleted_by_recipient')

            try:
                message = Message.objects.filter(pk=message_id)
                message_instance = message[0]
                result = list(message.values('id', *query_data))
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

            if result[0]['recipient'] == request.user.id and result[0]['is_deleted_by_recipient'] == False:
                if message_instance.is_unread:
                    message_instance.is_unread = False
                    message_instance.save()
            elif not (result[0]['sender'] == request.user.id and result[0]['is_deleted_by_sender'] == False):
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

            if not 'is_deleted_by_sender' in cleaned_data['column']:
                for each in result:
                    del each['is_deleted_by_sender']

            if not 'is_deleted_by_recipient' in cleaned_data['column']:
                for each in result:
                    del each['is_deleted_by_recipient']

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

        if message.sender != request.user and message.recipient != request.user:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        if message.sender == request.user:
            message.is_deleted_by_sender = True
            message.save()

        if message.recipient == request.user:
            message.is_deleted_by_recipient = True
            message.save()

        if message.is_deleted_by_sender and message.is_deleted_by_recipient:
            message.delete()

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })


class MessageView(View):

    def get(self, request, box_name='inbox', page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        context = {}
        result = Message.objects.none()
        if box_name == 'inbox':
            result = Message.objects.filter(
                recipient=request.user, is_deleted_by_recipient=False).order_by('-id')
            context['page_name'] = 'Message Inbox'

        elif box_name == 'outbox':
            result = Message.objects.filter(
                sender=request.user, is_deleted_by_sender=False).order_by('-id')
            context['page_name'] = 'Message Outbox'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('site_message/index.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['username'] = request.user.name
        context['box_name'] = box_name
        context['hide_welcome'] = True
        context['page_obj'] = page_obj

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


class MessageDetailView(View):

    def get(self, request, message_id):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        messsage_api = MessageAPI()
        request._body = json.dumps({
            "column": ["title", "send_date", "sender", "recipient", "content", "is_unread"]
        })
        result = json.loads(messsage_api.get(request, message_id).content)

        context = {}
        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['username'] = request.user.name
        context['hide_welcome'] = True

        if 'status' in result:
            if result['status'] == 200 and 'data' in result:
                if result['data']:
                    context['status'] = 200
                    context['message_id'] = message_id
                    context['title'] = result['data'][0]['title']
                    context['send_date'] = datetime.strptime(
                        result['data'][0]['send_date'], '%Y-%m-%dT%H:%M:%S.%f%z')
                    context['sender'] = User.objects.filter(
                        pk=result['data'][0]['sender'])[0]
                    context['recipient'] = User.objects.filter(
                        pk=result['data'][0]['recipient'])[0]
                    if context['sender'] == request.user:
                        context['box_name'] = 'outbox'
                        context['page_name'] = 'Message Outbox'
                    else:
                        context['box_name'] = 'inbox'
                        context['page_name'] = 'Message Inbox'
                    context['content'] = result['data'][0]['content']
                    context['is_unread'] = result['data'][0]['is_unread']
            else:
                context['status'] = result['status']
                if 'message' in result:
                    context['message'] = result['message']
        else:
            context['status'] = 500

        template = loader.get_template('site_message/detail.html')

        return HttpResponse(template.render(context, request))


class MessageSendView(View):

    def get(self, request):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        context = {}
        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['username'] = request.user.name
        context['page_name'] = 'Send a Message'
        context['hide_welcome'] = True

        template = loader.get_template('site_message/send.html')

        return HttpResponse(template.render(context, request))
