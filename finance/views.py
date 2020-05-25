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
from site_log.models import Log

from .models import Bill, CouponCode, RedemptionCode


class BillListAPI(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

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

        form = BillListAPIGetForm(request.GET)
        if form.is_valid():
            cleaned_data = form.clean()

            if cleaned_data['offset'] is None:
                cleaned_data['offset'] = 0
            if cleaned_data['limit'] is None:
                cleaned_data['limit'] = 10

            if request.user.is_superuser:
                result = list(Bill.objects.all()[
                    cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))
            else:
                result = list(Bill.objects.filter(user=request.user)[
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
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden',
            }, status=403)

        class BillListAPIPostForm(Form):
            username = CharField()
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
                cleaned_data['username'] = User.objects.get(
                    username=cleaned_data['username'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'UserNotFound',
                }, status=400)

            try:
                with transaction.atomic():
                    bill = Bill(user=cleaned_data['username'], amount=cleaned_data['amount'], date=now(
                    ), info=cleaned_data['info'])
                    cleaned_data['username'].balance = cleaned_data['username'].balance + \
                        cleaned_data['amount']

                    bill.save()
                    cleaned_data['username'].save()
                    log = Log(user=request.user, date=now(),
                              operation='Create a bill (id:' + str(bill.id) + ')')
                    log.save()
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
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class BillAPIGetForm(Form):
            choices = (
                ("user", "user"),
                ("amount", "amount"),
                ("date", "date"),
                ("info", "info"),
            )
            column = MultipleChoiceField(choices=choices)

        form = BillAPIGetForm(request.GET)
        if form.is_valid():
            cleaned_data = form.clean()
            query_data = cleaned_data['column'].copy()
            if not 'user' in cleaned_data['column']:
                query_data.append('user')

            try:
                result = list(Bill.objects.filter(pk=bill_id).values(
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

            if result[0]['user'] != request.user.id and not request.user.is_superuser:
                return JsonResponse({
                    'status': 403,
                    'message': 'Forbidden'
                }, status=403)

            if not 'user' in cleaned_data['column']:
                for each in result:
                    del each['user']

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
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden',
            }, status=403)

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

            try:
                with transaction.atomic():
                    log = Log(user=request.user, date=now(
                    ), operation='Update info of the bill (id:' + str(bill.id) + ')')
                    log.save()
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


class RedeemRedemptionCodeAPI(View):

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class RedeemRedemptionCodeAPIPostForm(Form):
            username = CharField()
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
                cleaned_data['username'] = User.objects.get(
                    username=cleaned_data['username'])
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
                    cleaned_data['username'].balance = cleaned_data['username'].balance + \
                        redemption_code.amount
                    bill = Bill(user=cleaned_data['username'], amount=redemption_code.amount, date=now(
                    ), info='Redeem the redemption code ' + cleaned_data['code'])

                    redemption_code.save()
                    cleaned_data['username'].save()
                    bill.save()
                    log = Log(user=request.user, date=now(), operation='Redeem the redemption code ' +
                              cleaned_data['code'] + ' for the user (username:' + cleaned_data['username'].username + ')')
                    log.save()
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
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class RedemptionCodeListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("code", "code"),
                ("amount", "amount"),
                ("is_available", "is_available"),
            )
            column = MultipleChoiceField(choices=choices)

        form = RedemptionCodeListAPIGetForm(request.GET)
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
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

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

            try:
                with transaction.atomic():
                    redemption_code.save()
                    log = Log(user=request.user, date=now(
                    ), operation='Create a redemption code (id:' + str(redemption_code.id) + ')')
                    log.save()
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


class RedemptionCodeAPI(View):
    def get(self, request, redemption_code_id):
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class RedemptionCodeAPIGetForm(Form):
            choices = (
                ("code", "code"),
                ("amount", "amount"),
                ("is_available", "is_available"),
            )
            column = MultipleChoiceField(choices=choices)

        form = RedemptionCodeAPIGetForm(request.GET)
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
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

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

            if 'code' in data and cleaned_data['code'] != '':
                redemption_code.code = cleaned_data['code']

            if cleaned_data['amount'] is not None:
                redemption_code.amount = cleaned_data['amount']

            if 'is_available' in data:
                redemption_code.is_available = cleaned_data['is_available']

            try:
                with transaction.atomic():
                    redemption_code.save()
                    log = Log(user=request.user, date=now(
                    ), operation='Edit the redemption code (id:' + str(redemption_code.id) + ')')
                    log.save()
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

    def delete(self, request, redemption_code_id):
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        try:
            redemption_code = RedemptionCode.objects.get(pk=redemption_code_id)
        except Exception as e:
            return JsonResponse({
                'status': 404,
                'message': 'Not Found',
            }, status=404)

        try:
            with transaction.atomic():
                log = Log(user=request.user, date=now(), operation='Delete a redemption code (id:' +
                          str(redemption_code.id) + ' code:' + redemption_code.code + ')')
                log.save()
                redemption_code.delete()
        except Exception as e:
            return JsonResponse({
                'status': 500,
                'message': 'DatabaseError',
            }, status=500)

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })


class CouponCodeListAPI(View):
    def get(self, request):
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class CouponCodeListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("code", "code"),
                ("discount", "discount"),
            )
            column = MultipleChoiceField(choices=choices)

        form = CouponCodeListAPIGetForm(request.GET)
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
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

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
                CouponCode.objects.filter(code=cleaned_data['code']))

            if exist_coupon_code != []:
                return JsonResponse({
                    'status': 409,
                    'message': 'CodeAlreadyExisted'
                }, status=409)

            coupon_code = CouponCode(
                code=cleaned_data['code'], discount=cleaned_data['discount'])

            try:
                with transaction.atomic():
                    coupon_code.save()
                    log = Log(user=request.user, date=now(
                    ), operation='Create a coupon code (id:' + str(coupon_code.id) + ')')
                    log.save()
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


class CouponCodeAPI(View):
    def get(self, request, coupon_code_id):
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        class CouponCodeAPIGetForm(Form):
            choices = (
                ("code", "code"),
                ("discount", "discount"),
            )
            column = MultipleChoiceField(choices=choices)

        form = CouponCodeAPIGetForm(request.GET)
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
        if not request.user.is_superuser:
            return JsonResponse({
                'status': 403,
                'message': 'Forbidden'
            }, status=403)

        try:
            coupon_code = CouponCode.objects.get(pk=coupon_code_id)
        except Exception as e:
            return JsonResponse({
                'status': 404,
                'message': 'Not Found',
            }, status=404)

        try:
            with transaction.atomic():
                log = Log(user=request.user, date=now(), operation='Delete a coupon code (id:' +
                          str(coupon_code.id) + ' code:' + coupon_code.code + ')')
                log.save()
                coupon_code.delete()
        except Exception as e:
            return JsonResponse({
                'status': 500,
                'message': 'DatabaseError',
            }, status=500)

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
