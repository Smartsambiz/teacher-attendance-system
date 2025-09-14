from django.db import models
from django.contrib.auth.models import User

class SchoolCalender(models.Model):
    date = models.DateField(unique=True)
    is_school_day = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.date} - {'School Day' if self.is_school_day else 'No School'}"


class Klass(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    section = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} - {self.section}"
    

class Student(models.Model):
    GENDER_CHOICES = (('M', 'MALE'), ('F', 'FEMALE'))
    klass = models.ForeignKey(Klass, related_name='students', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    parent_name = models.CharField(max_length=100)
    parent_phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"
    

class DailyAttendance(models.Model):
    STATUS_CHOICES = (('present', 'Present'), ('absent', 'Absent'))

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default='absent')

    class Meta:
        unique_together = ('student', 'date') # prevent duplicate entry for a student on the same day

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"