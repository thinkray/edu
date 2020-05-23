from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse
from django.views import View

from account.models import User
from course.models import Course, CourseInstance
from finance.models import Bill, CouponCode, RedemptionCode
from site_log.models import Log


class AdminBalanceListView(View):

    def get(self, request, page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        if not request.user.is_superuser:
            raise PermissionDenied()

        context = {}
        result = User.objects.all()
        context['page_name'] = 'Balance List'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('dashboard/admin/balance_list.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True
        context['page_obj'] = page_obj

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num / 2)):
            if page_start - 1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num / 2) * 2):
            if page_end + 1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end - page_start < int(page_bar_num / 2) * 2:
            for i in range(int(page_bar_num / 2) * 2):
                if page_start - 1 >= 1 and page_end - page_start < int(page_bar_num / 2) * 2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end + 1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))


class UserBillListView(View):

    def get(self, request, page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        context = {}
        result = Bill.objects.filter(user=request.user)
        context['page_name'] = 'Bill List'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('dashboard/user/bill_list.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True
        context['page_obj'] = page_obj

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num / 2)):
            if page_start - 1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num / 2) * 2):
            if page_end + 1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end - page_start < int(page_bar_num / 2) * 2:
            for i in range(int(page_bar_num / 2) * 2):
                if page_start - 1 >= 1 and page_end - page_start < int(page_bar_num / 2) * 2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end + 1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))


class UserCalendarView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        context = {}
        result = User.objects.all()
        context['page_name'] = 'My Calendar'

        template = loader.get_template('dashboard/user/calendar.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True
        if request.user.is_superuser:
            context['teach_course'] = Course.objects.all()
        elif request.user.groups.filter(name='teacher').exists():
            context['teach_course'] = Course.objects.filter(
                teacher=request.user)
        else:
            context['teach_course'] = []

        return HttpResponse(template.render(context, request))


class AdminCalendarView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        if not request.user.is_superuser:
            raise PermissionDenied()

        context = {}
        result = User.objects.all()
        context['page_name'] = 'Admin Calendar'

        template = loader.get_template('dashboard/admin/calendar.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True
        context['teach_course'] = Course.objects.all()

        return HttpResponse(template.render(context, request))


class UserCourseView(View):

    def get(self, request, panel_name='student', page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        context = {}
        if panel_name == 'study':
            result = CourseInstance.objects.filter(student=request.user)
            context['status'] = 200
            context['course_enroll_num'] = len(result)
            context['page_name'] = 'My Course | Study'
        elif panel_name == 'teaching':
            if request.user.groups.filter(name='teacher').exists() or request.user.is_superuser:
                context['status'] = 200
                result = Course.objects.filter(teacher=request.user)
                context['course_enroll_num'] = len(result)
                context['page_name'] = 'My Course | Teaching'
            else:
                result = []
                context['status'] = 403
        else:
            result = []
            context['status'] = 404

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('dashboard/user/course.html')

        context['site_name'] = settings.SITE_NAME
        context['panel_name'] = panel_name
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True
        context['page_obj'] = page_obj

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num / 2)):
            if page_start - 1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num / 2) * 2):
            if page_end + 1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end - page_start < int(page_bar_num / 2) * 2:
            for i in range(int(page_bar_num / 2) * 2):
                if page_start - 1 >= 1 and page_end - page_start < int(page_bar_num / 2) * 2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end + 1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))


class AdminCourseView(View):

    def get(self, request, page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        if not request.user.is_superuser:
            raise PermissionDenied()

        context = {}
        result = Course.objects.all()
        context['status'] = 200
        context['course_enroll_num'] = len(result)
        context['page_name'] = 'Course List'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('dashboard/admin/course.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True
        context['page_obj'] = page_obj

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num / 2)):
            if page_start - 1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num / 2) * 2):
            if page_end + 1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end - page_start < int(page_bar_num / 2) * 2:
            for i in range(int(page_bar_num / 2) * 2):
                if page_start - 1 >= 1 and page_end - page_start < int(page_bar_num / 2) * 2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end + 1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))


class AdminBillListView(View):

    def get(self, request, page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        if not request.user.is_superuser:
            raise PermissionDenied()

        context = {}
        result = Bill.objects.all()
        context['page_name'] = 'Bill List'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('dashboard/admin/bill_list.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True
        context['page_obj'] = page_obj

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num / 2)):
            if page_start - 1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num / 2) * 2):
            if page_end + 1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end - page_start < int(page_bar_num / 2) * 2:
            for i in range(int(page_bar_num / 2) * 2):
                if page_start - 1 >= 1 and page_end - page_start < int(page_bar_num / 2) * 2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end + 1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))


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
        context['page_name'] = 'User List'

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
        context['name'] = request.user.name
        context['username'] = request.user.username
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


class AdminOverviewView(View):

    def get(self, request, page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        if not request.user.is_superuser:
            raise PermissionDenied()

        context = {}
        result = Log.objects.all()
        context['page_name'] = 'Admin Dashboard'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('dashboard/admin/dashboard.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True
        context['page_obj'] = page_obj

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num / 2)):
            if page_start - 1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num / 2) * 2):
            if page_end + 1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end - page_start < int(page_bar_num / 2) * 2:
            for i in range(int(page_bar_num / 2) * 2):
                if page_start - 1 >= 1 and page_end - page_start < int(page_bar_num / 2) * 2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end + 1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))


class UserOverviewView(View):

    def get(self, request):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        context = {}
        result = CourseInstance.objects.filter(student=request.user)
        context['page_name'] = 'My Dashboard'

        template = loader.get_template('dashboard/user/dashboard.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True

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
        context['page_name'] = 'Redemption Code List'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template(
            'dashboard/admin/redemption_code_list.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
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
        context['name'] = request.user.name
        context['username'] = request.user.username
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


class UserLogListView(View):

    def get(self, request, page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        context = {}
        result = Log.objects.filter(user=request.user)
        context['page_name'] = 'Log List'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('dashboard/user/log_list.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True
        context['page_obj'] = page_obj

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num / 2)):
            if page_start - 1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num / 2) * 2):
            if page_end + 1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end - page_start < int(page_bar_num / 2) * 2:
            for i in range(int(page_bar_num / 2) * 2):
                if page_start - 1 >= 1 and page_end - page_start < int(page_bar_num / 2) * 2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end + 1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))


class AdminLogListView(View):

    def get(self, request, page=1):
        if not request.user.is_authenticated:
            response = redirect(reverse('user_login_view'))
            response['Location'] += '?redirect_uri=' + request.path
            return response

        if not request.user.is_superuser:
            raise PermissionDenied()

        context = {}
        result = Log.objects.all()
        context['page_name'] = 'Log List'

        paginator = Paginator(result, 10)
        page_obj = paginator.get_page(page)

        template = loader.get_template('dashboard/admin/log_list.html')

        context['site_name'] = settings.SITE_NAME
        context['is_authenticated'] = True
        context['is_superuser'] = request.user.is_superuser
        context['is_teacher'] = request.session.get('is_teacher')
        context['name'] = request.user.name
        context['username'] = request.user.username
        context['hide_welcome'] = True
        context['page_obj'] = page_obj

        page_start = page_obj.number
        page_bar_num = 5
        for i in range(int(page_bar_num / 2)):
            if page_start - 1 > 0:
                page_start = page_start - 1
        page_end = page_start
        for i in range(int(page_bar_num / 2) * 2):
            if page_end + 1 <= page_obj.paginator.num_pages:
                page_end = page_end + 1
        if page_end - page_start < int(page_bar_num / 2) * 2:
            for i in range(int(page_bar_num / 2) * 2):
                if page_start - 1 >= 1 and page_end - page_start < int(page_bar_num / 2) * 2:
                    page_start = page_start - 1
        page_bar = []
        for i in range(page_start, page_end + 1):
            page_bar.append(i)
        context['page_bar'] = page_bar

        return HttpResponse(template.render(context, request))
