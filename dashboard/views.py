from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse
from django.views import View

from account.models import User
from finance.models import CouponCode, RedemptionCode

class AdminUserListView(View):

    def get(self, request, page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        if not request.user.is_superuser:
            raise PermissionDenied()

        context = {}
        result = User.objects.all()
        context['page_name'] = 'Coupon Code List'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)
        result = []
        for each in page_obj:
            row = {}
            row['id'] = each.id
            row['username'] = each.username
            row['name'] = each.name
            row['is_teacher'] = each.groups.filter(name='teacher').exists()
            row['is_superuser'] = each.is_superuser
            row['last_login'] = each.last_login
            result.append(row)

        template = loader.get_template('dashboard/admin/user_list.html')
        
        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['username'] = request.user.name
        context['hide_welcome'] = True
        context['page_obj'] = page_obj
        context['result'] = result

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

class AdminRedemptionCodeListView(View):

    def get(self, request, page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        if not request.user.is_superuser:
            raise PermissionDenied()

        context = {}
        result = RedemptionCode.objects.all()
        context['page_name'] = 'Coupon Code List'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('dashboard/admin/redemption_code_list.html')
        
        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['username'] = request.user.name
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

class AdminCouponCodeListView(View):

    def get(self, request, page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        if not request.user.is_superuser:
            raise PermissionDenied()

        context = {}
        result = CouponCode.objects.all()
        context['page_name'] = 'Coupon Code List'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('dashboard/admin/coupon_code_list.html')
        
        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['username'] = request.user.name
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
