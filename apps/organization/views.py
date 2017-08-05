from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, JsonResponse
import json
from .models import CourseOrg, CityDict, Teacher
from courses.models import Course
from .forms import UserAskForm
from operation.models import UserFavorite
# Create your views here.



class OrgView(View):
    """
    课程机构列表
    """
    def get(self, request):
        # 课程机构
        all_orgs = CourseOrg.objects.all()
        hot_orgs = all_orgs.order_by('click_nums')[:3]
        # 城市
        all_citys = CityDict.objects.all()
        #搜索
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_orgs = all_orgs.filter(Q(name__icontains=search_keywords)|
                                             Q(desc__icontains = search_keywords))
        # 取出筛选城市
        city_id = request.GET.get('city', '')
        if city_id:
            all_orgs = all_orgs.filter(city=int(city_id))
        # 类别筛选
        category = request.GET.get('ct', '')
        if category:
            all_orgs = all_orgs.filter(category=category)
        # 排序
        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'students':
                all_orgs = all_orgs.order_by('-students')
            if sort == 'courses':
                all_orgs = all_orgs.order_by('-click_nums')

        org_nums = all_orgs.count()
        # 分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_orgs, 1, request=request)
        orgs = p.page(page)

        return render(request, 'org-list.html', {'orgs': orgs,
                                                 'all_citys': all_citys,
                                                 'org_nums': org_nums,
                                                 'city_id': city_id,
                                                 'category': category,
                                                 'hot_orgs': hot_orgs,
                                                 'sort': sort})


class AddUserAskView(View):
    """
    用户添加资讯
    """
    def post(self, request):
        userask_form = UserAskForm(request.POST)
        if userask_form.is_valid():
            userask_form.save(commit=True)
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            data = {'status': 'fail', 'msg': '添加出错'}
            data = json.dumps(data)
            return HttpResponse(data, content_type='application/json')


class OrgHomeView(View):
    """
    机构首页
    """
    def get(self, request, org_id):
        current_page = 'home'
        course_org = CourseOrg.objects.get(id=org_id)
        course_org.click_nums += 1
        course_org.save()
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        all_courses = course_org.course_set.all()[:3]
        all_teachers = course_org.teacher_set.all()[:3]
        return render(request, 'org-detail-homepage.html', {
            'all_courses': all_courses,
            'all_teachers': all_teachers,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav
        })


class OrgCourseView(View):
    """
    机构课程列表
    """
    def get(self, request, org_id):
        current_page = 'course'
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        all_courses = course_org.course_set.all()
        return render(request, 'org-detail-course.html', {
            'all_courses': all_courses,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav
        })


class OrgDescView(View):
    """
    机构介绍
    """
    def get(self, request, org_id):
        current_page = 'desc'
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-desc.html', {
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav
        })


class OrgTeacherView(View):
    """
    机构教师列表
    """
    def get(self, request, org_id):
        current_page = 'teacher'
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        all_teachers = course_org.teacher_set.all()
        return render(request, 'org-detail-teachers.html', {
            'all_teachers': all_teachers,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav
        })


class AddFavView(View):
    """
    用户收藏，取消收藏
    """
    def post(self, request):
        fav_id = request.POST.get('fav_id', 0)
        fav_type = request.POST.get('fav_type', 0)

        if not request.user.is_authenticated():
            return JsonResponse({'status': 'fail', 'msg': '用户未登录'})

        exist_records = UserFavorite.objects.filter(user=request.user, fav_id=int(fav_id), fav_type=int(fav_type))
        if exist_records:
            exist_records.delete()
            if int(fav_type) == 1:
                course = Course.objects.get(id=int(fav_id))
                course.fav_nums -= 1
                course.save()
            elif int(fav_type) == 2:
                course_org = CourseOrg.objects.get(id=int(fav_id))
                course_org.fav_nums -= 1
                course_org.save()
            elif int(fav_type) == 3:
                teacher = Teacher.objects.get(id=int(fav_id))
                teacher.fav_nums -= 1
                teacher.save()
            return JsonResponse({'status': 'success', 'msg': '收藏'})
        else:
            user_fav = UserFavorite()
            if int(fav_id) > 0 and int(fav_type) > 0:
                user_fav.user = request.user
                user_fav.fav_id = int(fav_id)
                user_fav.fav_type = int(fav_type)
                user_fav.save()
                if int(fav_type) == 1:
                    course = Course.objects.get(id=int(fav_id))
                    course.fav_nums += 1
                    course.save()
                elif int(fav_type) == 2:
                    course_org = CourseOrg.objects.get(id=int(fav_id))
                    course_org.fav_nums += 1
                    course_org.save()
                elif int(fav_type) == 3:
                    teacher = Teacher.objects.get(id=int(fav_id))
                    teacher.fav_nums += 1
                    teacher.save()
                return JsonResponse({'status': 'success', 'msg': '已收藏'})
            else:
                return JsonResponse({'status': 'fail', 'msg': '收藏出错'})


class TeacherListView(View):
    """
    讲师列表
    """
    def get(self, request):
        all_teachers = Teacher.objects.all()
        hot_teachers = Teacher.objects.all().order_by('-click_nums')[:3]
        #搜索
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_teachers = all_teachers.filter(Q(name__icontains=search_keywords)|
                                             Q(work_company__icontains = search_keywords)|
                                            Q(work_position__icontains=search_keywords))
        # 排序
        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'hot':
                all_teachers = all_teachers.order_by('-click_nums')

        # 分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_teachers, 1, request=request)
        teachers = p.page(page)

        return render(request, 'teachers-list.html', {
            'teachers': teachers,
            'hot_teachers': hot_teachers,
            'sort': sort
        })


class TeacherDetailView(View):
    """
    讲师详情
    """
    def get(self, request, teacher_id):
        teacher = get_object_or_404(Teacher, id=teacher_id)
        hot_teachers = Teacher.objects.all().order_by('-click_nums')[:3]
        teacher.click_nums += 1
        teacher.save()
        all_courses = teacher.course_set.all()

        has_teacher_fav = False
        has_org_fav = False
        if UserFavorite.objects.filter(user=request.user, fav_id=teacher.id, fav_type=3):
            has_teacher_fav =True
        if UserFavorite.objects.filter(user=request.user, fav_id=teacher.org.id, fav_type=2):
            has_org_fav = True

        return render(request, 'teacher-detail.html', {
            'teacher': teacher,
            'hot_teachers': hot_teachers,
            'all_courses': all_courses,
            'has_teacher_fav': has_teacher_fav,
            'has_org_fav': has_org_fav
        })