from django.db import transaction
from django.views import View
from django.utils.timezone import localtime, now
from django.forms import Form, IntegerField, MultipleChoiceField, DateTimeField, CharField, DecimalField
from django.shortcuts import render
from django.http import JsonResponse
from account.models import User
from .models import Bill, RedemptionCode, CouponCode
import json


class BillListAPI(View):
    def get(self, request):
        class BillListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("user", "user"),
                ("amount", "amount"),
                ("date", "date"),
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

        form = BillListAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            if cleaned_data['offset'] is None:
                cleaned_data['offset'] = 0
            if cleaned_data['limit'] is None:
                cleaned_data['limit'] = 10

            result = list(Bill.objects.all()[
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
        class BillListAPIPostForm(Form):
            user = IntegerField()
            amount = DecimalField(max_digits=17, decimal_places=2)
            info = CharField(required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = BillListAPIPostForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                cleaned_data['user'] = User.objects.get(
                    pk=cleaned_data['user'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'UserNotFound',
                }, status=400)

            try:
                with transaction.atomic():
                    bill = Bill(user=cleaned_data['user'], amount=cleaned_data['amount'], date=now(
                    ), info=cleaned_data['info'])
                    cleaned_data['user'].balance = cleaned_data['user'].balance + \
                        cleaned_data['amount']

                    bill.save()
                    cleaned_data['user'].save()
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


class BillAPI(View):
    def get(self, request, bill_id):
        class BillAPIGetForm(Form):
            choices = (
                ("user", "user"),
                ("amount", "amount"),
                ("date", "date"),
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

        form = BillAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                result = list(Bill.objects.filter(pk=bill_id).values(
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

    def patch(self, request, bill_id):
        class BillAPIPatchForm(Form):
            info = CharField(required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = BillAPIPatchForm(data)
        if form.is_valid():
            try:
                bill = Bill.objects.get(
                    pk=bill_id)
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            cleaned_data = form.clean()

            if 'info' in data:
                bill.info = cleaned_data['info']

            bill.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success',
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)


class RedeemRedemptionCodeAPI(View):

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class RedemptionCodeListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class RedemptionCodeAPI(View):
    def get(self, request, redemption_code_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def patch(self, request, redemption_code_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def delete(self, request, redemption_code_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class CouponCodeListAPI(View):
    def get(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def post(self, request):
        return JsonResponse({
            'error': 'NotImplementedError'
        })


class CouponCodeAPI(View):
    def get(self, request, coupon_code_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })

    def delete(self, request, coupon_code_id):
        return JsonResponse({
            'error': 'NotImplementedError'
        })
