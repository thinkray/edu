import json

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import transaction
from django.forms import (
    BooleanField, CharField, DateTimeField, DecimalField, Form, IntegerField,
    MultipleChoiceField)
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import localtime, now
from django.views import View

from account.models import User

from .models import Bill, CouponCode, RedemptionCode


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
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class RedeemRedemptionCodeAPIPostForm(Form):
            user = IntegerField()
            code = CharField()

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = RedeemRedemptionCodeAPIPostForm(data)
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
                redemption_code = RedemptionCode.objects.get(
                    code=cleaned_data['code'])
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            if redemption_code.is_available == False:
                return JsonResponse({
                    'status': 403,
                    'message': 'AlreadyRedeemed',
                }, status=403)

            try:
                with transaction.atomic():
                    redemption_code.is_available = False
                    cleaned_data['user'].balance = cleaned_data['user'].balance + \
                        redemption_code.amount
                    bill = Bill(user=cleaned_data['user'], amount=redemption_code.amount, date=now(
                    ), info='Redeem the redemption code ' + cleaned_data['code'])

                    redemption_code.save()
                    cleaned_data['user'].save()
                    bill.save()
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


class RedemptionCodeListAPI(View):
    def get(self, request):
        class RedemptionCodeListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("code", "code"),
                ("amount", "amount"),
                ("is_available", "is_available"),
            )
            column = MultipleChoiceField(choices=choices)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = RedemptionCodeListAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            if cleaned_data['offset'] is None:
                cleaned_data['offset'] = 0
            if cleaned_data['limit'] is None:
                cleaned_data['limit'] = 10

            result = list(RedemptionCode.objects.all()[
                          cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))

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
        class RedemptionCodeListAPIPostForm(Form):
            code = CharField()
            amount = DecimalField(max_digits=17, decimal_places=2, validators=[
                                  MinValueValidator(0)])

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = RedemptionCodeListAPIPostForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            exist_redemption_code = list(
                RedemptionCode.objects.filter(code=cleaned_data['code']))

            if exist_redemption_code != []:
                return JsonResponse({
                    'status': 409,
                    'message': 'CodeAlreadyExisted'
                }, status=409)

            redemption_code = RedemptionCode(
                code=cleaned_data['code'], amount=cleaned_data['amount'], is_available=True)

            redemption_code.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success'
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)


class RedemptionCodeAPI(View):
    def get(self, request, redemption_code_id):
        class RedemptionCodeAPIGetForm(Form):
            choices = (
                ("code", "code"),
                ("amount", "amount"),
                ("is_available", "is_available"),
            )
            column = MultipleChoiceField(choices=choices)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = RedemptionCodeAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                result = list(RedemptionCode.objects.filter(pk=redemption_code_id).values(
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

    def patch(self, request, redemption_code_id):
        class RedemptionCodeAPIPatchForm(Form):
            code = CharField(required=False)
            amount = DecimalField(max_digits=17, decimal_places=2, validators=[
                                  MinValueValidator(0)], required=False)
            is_available = BooleanField(required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = RedemptionCodeAPIPatchForm(data)
        if form.is_valid():
            try:
                redemption_code = RedemptionCode.objects.get(
                    pk=redemption_code_id)
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            cleaned_data = form.clean()

            if 'code' in data and cleaned_data['amount'] != '':
                redemption_code.code = cleaned_data['code']

            if cleaned_data['amount'] is not None:
                redemption_code.amount = cleaned_data['amount']

            if 'is_available' in data:
                redemption_code.is_available = cleaned_data['is_available']

            redemption_code.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success',
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def delete(self, request, redemption_code_id):
        try:
            redemption_code = RedemptionCode.objects.get(pk=redemption_code_id)
        except Exception as e:
            return JsonResponse({
                'status': 404,
                'message': 'Not Found',
            }, status=404)

        redemption_code.delete()

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })


class CouponCodeListAPI(View):
    def get(self, request):
        class CouponCodeListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("code", "code"),
                ("discount", "discount"),
            )
            column = MultipleChoiceField(choices=choices)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = CouponCodeListAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            if cleaned_data['offset'] is None:
                cleaned_data['offset'] = 0
            if cleaned_data['limit'] is None:
                cleaned_data['limit'] = 10

            result = list(CouponCode.objects.all()[
                          cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))

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
        class CouponCodeListAPIPostForm(Form):
            code = CharField()
            discount = DecimalField(max_digits=2, decimal_places=2, validators=[
                MinValueValidator(0.001), MaxValueValidator(0.999)])

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = CouponCodeListAPIPostForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            exist_coupon_code = list(
                RedemptionCode.objects.filter(code=cleaned_data['code']))

            if exist_coupon_code != []:
                return JsonResponse({
                    'status': 409,
                    'message': 'CodeAlreadyExisted'
                }, status=409)

            coupon_code = CouponCode(
                code=cleaned_data['code'], discount=cleaned_data['discount'])

            coupon_code.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success'
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)


class CouponCodeAPI(View):
    def get(self, request, coupon_code_id):
        class CouponCodeAPIGetForm(Form):
            choices = (
                ("code", "code"),
                ("discount", "discount"),
            )
            column = MultipleChoiceField(choices=choices)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = CouponCodeAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                result = list(CouponCode.objects.filter(pk=coupon_code_id).values(
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

    def delete(self, request, coupon_code_id):
        try:
            coupon_code = CouponCode.objects.get(pk=coupon_code_id)
        except Exception as e:
            return JsonResponse({
                'status': 404,
                'message': 'Not Found',
            }, status=404)

        coupon_code.delete()

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })


class CouponCodeCheckAPI(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class CouponCodeCheckAPIPostForm(Form):
            code = CharField()

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = CouponCodeCheckAPIPostForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            coupon_code = list(CouponCode.objects.filter(
                code=cleaned_data['code']).values())

            if coupon_code == []:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            return JsonResponse({
                'status': 200,
                'message': 'Success',
                'data': coupon_code
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)
