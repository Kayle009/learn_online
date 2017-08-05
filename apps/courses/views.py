from django.shortcuts import render, get_object_or_404
from django.views.generic.base import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.db.models import Q

from utils.mixin_utils import LoginRequiredMixin
from .models import Course, Video
from operation.models import UserFavorite, CourseComments, UserCourse
# Create your views here.


class CourseListView(View):
    """
    课程列表
    """
    def get(self, request):
        all_courses = Course.objects.all().order_by('-add_time')
        hot_courses = Course.objects.all().order_by('-click_nums')[:3]

        #搜索
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_courses = all_courses.filter(Q(name__icontains=search_keywords)|
                                             Q(desc__icontains = search_keywords)|
                                             Q(detail__icontains=search_keywords))

        # 排序
        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'students':
                all_courses = all_courses.order_by('-students')
            if sort == 'hot':
                all_courses = all_courses.order_by('-click_nums')

        # 分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_courses, 3, request=request)
        courses = p.page(page)

        return render(request, 'course-list.html', {
            'courses': courses,
            'sort': sort,
            'hot_courses': hot_courses
        })


class CourseDetailView(View):
    """
    课程详情
    """
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        course.click_nums += 1
        course.save()

        has_fav_course = False
        has_fav_org = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course.id, fav_type=1):
                has_fav_course = True
            if UserFavorite.objects.filter(user=request.user, fav_id=course.course_org.id, fav_type=2):
                has_fav_org = True

        tag = course.tag
        if tag:
            relate_course = Course.objects.filter(tag=tag).exclude(id=course.id).order_by('-click_nums')[:1]
        else:
            relate_course = []
        return render(request, 'course-detail.html', {
            'course': course,
            'relate_course': relate_course,
            'has_fav_course': has_fav_course,
            'has_fav_org': has_fav_org
        })


class CourseInfoView(LoginRequiredMixin, View):
    """
    课程章节
    """
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        course.click_nums += 1
        course.save()

        user_course = UserCourse.objects.filter(user=request.user, course=course)
        if not user_course:
            user_course = UserCourse(user=request.user, course=course)
            user_course.save()
            course.students += 1
            course.save()


        # 取出学习这门课程的所有用户的课程
        user_courses = UserCourse.objects.filter(course=course)
        all_users = [user.user for user in user_courses]
        all_user_courses = UserCourse.objects.filter(user__in=all_users)
        courses_ids = [user_course.course.id for user_course in all_user_courses]
        relate_courses = Course.objects.filter(id__in=courses_ids).exclude(id=course.id).order_by('-click_nums')[:3]
        return render(request, 'course-video.html', {
            'course': course,
            'relate_courses': relate_courses
        })


class CourseCommentView(LoginRequiredMixin, View):
    """
    课程评论
    """
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        all_comments = course.coursecomments_set.all()

        user_course = UserCourse.objects.filter(user=request.user, course=course)
        if not user_course:
            user_course = UserCourse(user=request.user, course=course)
            user_course.save()
            course.students += 1
            course.save()

        # 取出学习这门课程的所有用户的课程
        user_courses = UserCourse.objects.filter(course=course)
        all_users = [user.user for user in user_courses]
        all_user_courses = UserCourse.objects.filter(user__in=all_users)
        courses_ids = [user_course.course.id for user_course in all_user_courses]
        relate_courses = Course.objects.filter(id__in=courses_ids).exclude(id=course.id).order_by('-click_nums')[:3]
        return render(request, 'course-comment.html', {
            'course': course,
            'all_comments': all_comments,
            'relate_courses': relate_courses
        })


class AddCommentsView(View):
    """
    用户添加评论
    """
    def post(self, request):
        if not request.user.is_authenticated():
            return JsonResponse({'status': 'fail', 'msg': '用户未登录'})

        course_id = request.POST.get('course_id', 0)
        comments = request.POST.get('comments', '')
        if int(course_id) > 0 and comments:
            course_comments = CourseComments()
            course = Course.objects.get(id=int(course_id))
            course_comments.course = course
            course_comments.comments = comments
            course_comments.user = request.user
            course_comments.save()
            return JsonResponse({'status': 'success', 'msg': '添加成功'})
        else:
            return JsonResponse({'status': 'fail', 'msg': '添加失败'})


class VideoPlayView(LoginRequiredMixin, View):
    """
    视频播放
    """
    def get(self, request, video_id):
        video = get_object_or_404(Video, id=video_id)
        course = video.lesson.course


        user_course = UserCourse.objects.filter(user=request.user, course=course)
        if not user_course:
            user_course = UserCourse(user=request.user, course=course)
            user_course.save()
            course.students += 1
            course.save()

        # 取出学习这门课程的所有用户的课程
        user_courses = UserCourse.objects.filter(course=course)
        all_users = [user.user for user in user_courses]
        all_user_courses = UserCourse.objects.filter(user__in=all_users)
        courses_ids = [user_course.course.id for user_course in all_user_courses]
        relate_courses = Course.objects.filter(id__in=courses_ids).exclude(id=course.id).order_by('-click_nums')[:3]
        return render(request, 'course-play.html', {
            'course': course,
            'relate_courses': relate_courses,
            'video': video
        })
