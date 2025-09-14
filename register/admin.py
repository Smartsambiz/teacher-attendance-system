from django.contrib import admin
from .models import SchoolCalender, Klass, Student, DailyAttendance

admin.site.register(SchoolCalender)
admin.site.register(Klass)
admin.site.register(Student)
admin.site.register(DailyAttendance)
