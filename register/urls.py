from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import auth


router = DefaultRouter()
router.register(r'classes', views.KlassViewSet, basename='klass')
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'attendance', views.DailyAttendanceViewSet, basename='attendance')
router.register(r'calender', views.SchoolCalenderViewSet, basename='schoolcalender')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', auth.login_view, name='login'),
    path('auth/logout/', auth.logout_view, name='logout'),
    path('debug/csrf/', views.debug_csfr, name='debug_csrf'),
    path('attendance/debug_simple/', views.DailyAttendanceViewSet.as_view({'get': 'debug_simple'}), name='debug_simple'),
    path('schoolcalender/set_day/', views.SchoolCalenderViewSet.as_view({'post': 'set_day'}), name='set_day'),
]