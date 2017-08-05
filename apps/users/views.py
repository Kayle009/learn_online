from django.shortcuts import render, render_to_response
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.views.generic.base import View
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponseRedirect
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger


from .models import UserProfile, EmailVerifyRecord
from operation.models import UserCourse, UserFavorite, UserMessage
from .forms import LoginForm, RegisterForm, ForgetPwdForm, ModifyPwdForm, UploadImageForm, UserInfoForm
from utils.email_send import send_register_email
from utils.mixin_utils import LoginRequiredMixin
from organization.models import CourseOrg
from courses.models import Course, Teacher
from .models import Banner
# Create your views here.


class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = UserProfile.objects.get(Q(username=username)|Q(email=username))
            if user.check_password(password):
                return user
        except Exception as e:
            return None


def page_not_found(request):
    response = render_to_response('404.html', {})
    response.status_code = 404
    return response


def page_error(request):
    response = render_to_response('500.html', {})
    response.status_code = 500
    return response


class IndexView(View):
    def get(self, request):
        all_banners = Banner.objects.all().order_by('index')
        courses = Course.objects.filter(is_banner=False)[:6]
        banner_course = Course.objects.filter(is_banner=True)
        course_orgs = CourseOrg.objects.all()[:15]
        return render(request, 'index.html', {
            'all_banners': all_banners,
            'courses': courses,
            'banner_course': banner_course,
            'course_orgs': course_orgs
        })


class ActiveView(View):

    def get(self, request, active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                user = UserProfile.objects.get(email=email)
                user.is_active = True
                user.save()
        else:
            return render(request, 'active_fail.html')
        return render(request, 'login.html')


class RegisterView(View):

    def get(self, request):
        register_form = RegisterForm()
        return render(request, 'register.html', {'register_form': register_form})

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            user_name = request.POST.get('email', '')
            if UserProfile.objects.filter(email=user_name):
                return render(request, 'register.html', {'register_form': register_form, 'msg': '用户已存在'})
            pass_word = request.POST.get('password', '')
            user_profile = UserProfile()
            user_profile.username = user_name
            user_profile.email = user_name
            user_profile.is_active = False
            user_profile.password = make_password(password=pass_word)
            user_profile.save()

            user_message = UserMessage()
            user_message.user = user_profile.id
            user_message.message = '欢迎注册'
            user_message.save()

            send_register_email(user_name, 'register')
            return render(request, 'login.html')
        else:
            return render(request, 'register.html', {'register_form': register_form})


class LogoutView(View):

    def get(self, request):
        path = request.META.get('HTTP_REFERER')
        if path is None:
            path = '/'
        logout(request)
        return HttpResponseRedirect(path)

class LoginView(View):

    def get(self, request):
        refer = request.META.get('HTTP_REFERER')
        return render(request, 'login.html', {'refer': refer})

    def post(self, request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name = request.POST.get('username', '')
            pass_word = request.POST.get('password', '')
            user = authenticate(username=user_name, password=pass_word)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    path = request.POST.get('refer')
                    if path == 'None':
                        path = '/'
                    return HttpResponseRedirect(path)
                else:
                    return render(request, 'login.html', {'msg': '用户未激活!'})
            else:
                return render(request, 'login.html', {'msg': '用户名或密码错误!', 'login_form': login_form})
        else:
            return render(request, 'login.html', {'login_form': login_form})


class ForgetPwdView(View):

    def get(self, request):
        forget_form = ForgetPwdForm()
        return render(request, 'forgetpwd.html', {'forget_form': forget_form})

    def post(self, request):
        forget_form = ForgetPwdForm(request.POST)
        if forget_form.is_valid():
            email = request.POST.get('email', '')
            send_register_email(email, 'forget')
            return render(request, 'send_success.html')
        else:
            return render(request, 'forgetpwd.html', {'forget_form': forget_form})


class ResetPwdView(View):

    def get(self, request, reset_code):
        all_records = EmailVerifyRecord.objects.filter(code=reset_code)
        if all_records:
            for record in all_records:
                email = record.email
                return render(request, 'password_reset.html', {'email': email})
        else:
            return render(request, 'active_fail.html')
        return render(request, 'login.html')


class ModifyPwdView(View):

    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        email = request.POST.get('email', '')
        if modify_form.is_valid():
            pwd1 = request.POST.get('password1', '')
            pwd2 = request.POST.get('password2', '')
            if pwd1 != pwd2:
                return render(request, 'password_reset.html', {'email': email, 'msg': '密码不一致'})
            user = UserProfile.objects.get(email=email)
            user.password = make_password(pwd1)
            user.save()
            return render(request, 'login.html')
        else:
            return render(request, 'password_reset.html', {'email': email,'modify_form': modify_form})


class UserInfoView(LoginRequiredMixin, View):
    """用户个人信息"""
    def get(self, request):
        return render(request, 'usercenter-info.html', {})

    def post(self, request):
        user_form = UserInfoForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse(user_form.errors)




class UploadImageView(LoginRequiredMixin, View):
    """
    用户修改头像
    """
    def post(self, request):
        image_form = UploadImageForm(request.POST, request.FILES, instance=request.user)
        if image_form.is_valid():
            request.user.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'fail'})


class UpdatePwdView(View):
    """
    修改密码
    """
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get('password1', '')
            pwd2 = request.POST.get('password2', '')
            if pwd1 != pwd2:
                return JsonResponse({'status': 'fail', 'msg': '密码不一致'})
            user = request.user
            user.password = make_password(pwd1)
            user.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse(modify_form.errors)


class SendEmailCodeView(LoginRequiredMixin, View):
    """
    发送邮箱验证码
    """
    def get(self, request):
        email = request.GET.get('email', '')

        if UserProfile.objects.filter(email=email):
            return JsonResponse({'email': '邮箱已存在'})
        send_register_email(email, 'update_email')
        return JsonResponse({'statue': 'success'})


class UpdateEmailView(LoginRequiredMixin, View):
    """
    修改邮箱
    """
    def post(self, request):
        email = request.POST.get('email', '')
        code = request.POST.get('code', '')

        existed_records = EmailVerifyRecord.objects.filter(email=email, code=code, send_type='update_email')
        if existed_records:
            user = request.user
            user.email = email
            user.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': '验证码出错'})


class MyCourseView(LoginRequiredMixin, View):
    """
    我的课程
    """
    def get(self, request):
        user_courses = UserCourse.objects.filter(user=request.user)
        return render(request, 'usercenter-mycourse.html', {
            'user_courses': user_courses
        })


class MyFavOrgView(LoginRequiredMixin, View):
    """
    我的收藏-课程机构
    """
    def get(self, request):
        fav_orgs = UserFavorite.objects.filter(user=request.user, fav_type=2)
        org_ids = [fav_org.fav_id for fav_org in fav_orgs]
        org_list = CourseOrg.objects.filter(id__in=org_ids)
        return render(request, 'usercenter-fav-org.html', {
            'org_list': org_list
        })


class MyFavTeacherView(LoginRequiredMixin, View):
    """
    我的收藏-授课讲师
    """
    def get(self, request):
        fav_teachers = UserFavorite.objects.filter(user=request.user, fav_type=3)
        teacher_ids = [fav_teacher.fav_id for fav_teacher in fav_teachers]
        teacher_list = Teacher.objects.filter(id__in=teacher_ids)
        return render(request, 'usercenter-fav-teacher.html', {
            'teacher_list': teacher_list
        })


class MyFavCourseView(LoginRequiredMixin, View):
    """
    我的收藏-公开课程
    """
    def get(self, request):
        fav_courses = UserFavorite.objects.filter(user=request.user, fav_type=1)
        course_ids = [fav_course.fav_id for fav_course in fav_courses]
        course_list = Course.objects.filter(id__in=course_ids)
        return render(request, 'usercenter-fav-course.html', {
            'course_list': course_list
        })


class MyMessageView(LoginRequiredMixin, View):
    """
    我的消息
    """
    def get(self, request):
        all_message = UserMessage.objects.filter(user=request.user.id)
        # 分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_message, 1, request=request)
        messages = p.page(page)
        for message in messages.object_list:
            message.has_read = True
            message.save()
        return render(request, 'usercenter-message.html', {
            'messages': messages
        })