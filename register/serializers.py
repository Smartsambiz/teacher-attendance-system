from rest_framework import serializers
from .models import Klass, Student, DailyAttendance, SchoolCalender
from django.contrib.auth.models import User

class StudentSerializer(serializers.ModelSerializer):
    # This will show the class name instead of just the class ID
    klass_name = serializers.CharField(source='klass.__str__', read_only=True)
    

    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'gender', 'date_of_birth', 'parent_name', 'parent_phone', 'klass', 'klass_name']


class KlassSerializer(serializers.ModelSerializer):
    # This will nest the entire list of students within the class data
    students = StudentSerializer(many=True, read_only=True)

    # Show the teacher's username
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    teacher = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta: 
        model = Klass
        fields = ['id', 'name', 'section', 'teacher', 'teacher_name', 'students']


class DailyAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.__str__', read_only=True)

    class Meta: 
        model = DailyAttendance
        fields = ['id', 'student', 'student_name', 'date', 'status']


class SchoolCalenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolCalender
        fields = ['id', 'date', 'is_school_day', 'notes']