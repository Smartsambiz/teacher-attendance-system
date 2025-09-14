from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Q
from .models import Klass, Student, DailyAttendance, SchoolCalender
from .serializers import KlassSerializer, StudentSerializer, DailyAttendanceSerializer, SchoolCalenderSerializer
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.middleware.csrf import get_token
from calendar import weekday

def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def debug_csfr(request):
    """Debug endpoint to check CSRF token status"""
    from django.middleware.csrf import get_token
    return Response({
        'csrfToken': get_token(request),
        'session_id': request.session.session_key,
        'user_authenticated': request.user.is_authenticated,
        'request_headers': dict(request.headers),
       })


class KlassViewSet(viewsets.ModelViewSet):
    serializer_class = KlassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Klass.objects.filter(teacher=self.request.user)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)
        print("Class created:", serializer.data)

class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only students in classes owned by this teacher and optionally filtered by class
        klass_id = self.request.query_params.get('klass')
        base_qs = Student.objects.filter(klass__teacher=self.request.user)
        if klass_id:
            base_qs = base_qs.filter(klass__id=klass_id)
        return base_qs

    def perform_create(self, serializer):
        klass_id = self.request.data.get('klass')
        klass = Klass.objects.get(id=klass_id, teacher=self.request.user)
        serializer.save(klass=klass)
        print("Student created:", serializer.data)

class DailyAttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = DailyAttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DailyAttendance.objects.filter(student__klass__teacher=self.request.user)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        class_id = request.data.get('class_id')
        date = request.data.get('date')
        attendance_data = request.data.get('attendance', [])
        print("DEBUG POST DATA:", request.data)

        # Check if date is weekend
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        is_weekend = date_obj.weekday() in [5, 6]  # Saturday=5, Sunday=6

        # Validate the date is a school day
        try:
            calendar_entry, created = SchoolCalender.objects.get_or_create(
                date=date,
                defaults={'is_school_day': not is_weekend}
            )
            # If it's a weekend and not overridden, block attendance
            if is_weekend and not calendar_entry.is_school_day:
                return Response(
                    {"error": f"{date} is a weekend and not marked as a school day. Cannot save attendance."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not calendar_entry.is_school_day:
                return Response(
                    {"error": f"{date} is not a school day. Cannot save attendance."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {"error": f"Error checking school calendar: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        records_created = []
        errors = []

        for record in attendance_data:
            try:
                student = Student.objects.get(id=record['student_id'], klass__id=class_id)
                # Create or update the attendance record
                attendance_obj, created = DailyAttendance.objects.update_or_create(
                    student=student,
                    date=date,
                    defaults = {'status': record['status']}
                )
                records_created.append(DailyAttendanceSerializer(attendance_obj).data)
            except Student.DoesNotExist:
                errors.append(f"Student with id {record['student_id']} not found in class.")
            except Exception as e:
                errors.append(str(e))

        if errors:
            return Response({"errors": errors, "created": records_created}, status=status.HTTP_207_MULTI_STATUS)
        
        return Response(records_created, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def weekly_report(self, request):
        """Calculate weekly attendance for a class."""
        class_id = request.query_params.get('class_id')
        year = int(request.query_params.get('year', timezone.now().year))
        week = int(request.query_params.get('week', timezone.now().isocalendar()[1]))

        # Calculate start and end of the week
        start_date = datetime.fromisocalendar(year, week, 1).date()
        end_date = start_date + timedelta(days=6)
        
        print(f"📊 Weekly Report for Week {week}, {year}")
        print(f"   📅 Date Range: {start_date} to {end_date}")

        # Get all school days in that week
        school_days = SchoolCalender.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            is_school_day=True
        )
        
        print(f"   🏫 School days in week: {school_days.count()}")
        
        # Get all students in the class
        students = Student.objects.filter(klass__id=class_id)
        print(f"   👥 Students in class: {students.count()}")

        report = []
        
        for student in students:
            # Count presents for the student in the week
            presents = DailyAttendance.objects.filter(
                student=student,
                date__gte=start_date,
                date__lte=end_date,
                status='present'
            ).count()

            school_days_count = school_days.count()
            percentage = (presents / school_days_count * 100) if school_days_count > 0 else 0

            report.append({
                'student_id': student.id,
                'student_name': str(student),
                'presents': presents,
                'school_days': school_days_count,
                'percentage': round(percentage, 2)
            })
            
            if presents > 0:
                print(f"   ✅ {student}: {presents} presents")

        response_data = {
            'week': week,
            'year': year,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_school_days': school_days.count(),
            'report': report
        }
        
        print(f"   📈 Report generated with {len(report)} student entries")
        
        return Response(response_data)    
    

    

    # In your DailyAttendanceViewSet, add this action:
    @action(detail=False, methods=['get'])
    def termly_report(self, request):
        """Calculate comprehensive termly attendance report."""
        class_id = request.query_params.get('class_id')
        start_date_str = request.query_params.get('start_date', '2025-09-01')  # Default to term start
        end_date_str = request.query_params.get('end_date', '2025-12-15')     # Default to term end
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # Get the class
            klass = Klass.objects.get(id=class_id, teacher=request.user)
            
            # Get all school days in the term period
            school_days = SchoolCalender.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                is_school_day=True
            )
            
            # Get all non-school days (holidays, breaks)
            non_school_days = SchoolCalender.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                is_school_day=False
            )
            
            # Get all students in the class
            students = Student.objects.filter(klass=klass)
            
            term_report = {
                'term_period': f"{start_date} to {end_date}",
                'class_name': f"{klass.name} - {klass.section}",
                'attendance_summary': {
                    'total_school_days': school_days.count(),
                    'total_non_school_days': non_school_days.count(),
                    'total_days_in_period': (end_date - start_date).days + 1,
                },
                'students': [],
                'class_totals': {
                    'total_students': students.count(),
                    'total_possible_attendance': students.count() * school_days.count(),
                    'total_actual_attendance': 0,
                }
            }
            
            # Calculate attendance for each student
            for student in students:
                presents = DailyAttendance.objects.filter(
                    student=student,
                    date__gte=start_date,
                    date__lte=end_date,
                    status='present'
                ).count()
                
                percentage = (presents / school_days.count() * 100) if school_days.count() > 0 else 0
                
                term_report['class_totals']['total_actual_attendance'] += presents
                
                term_report['students'].append({
                    'student_id': student.id,
                    'student_name': f"{student.first_name} {student.last_name}",
                    'gender': student.gender,
                    'presents': presents,
                    'absences': school_days.count() - presents,
                    'attendance_rate': f"{round(percentage, 1)}%",
                    'status': 'Excellent' if percentage >= 90 else 
                            'Good' if percentage >= 75 else 
                            'Needs Improvement'
                })
            
            # Calculate class averages
            if students.count() > 0 and school_days.count() > 0:
                class_avg = (term_report['class_totals']['total_actual_attendance'] / 
                            term_report['class_totals']['total_possible_attendance']) * 100
                term_report['class_totals']['class_average'] = f"{round(class_avg, 1)}%"
            
            return Response(term_report)
            
        except Klass.DoesNotExist:
            return Response({"error": "Class not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        

    # Add to DailyAttendanceViewSet
    @action(detail=False, methods=['get'])
    def debug_class_attendance(self, request):
        """Debug: Get all attendance records for a class"""
        class_id = request.query_params.get('class_id')
        
        if not class_id:
            return Response({"error": "class_id parameter required"}, status=400)
        
        # Get all attendance records for this class
        attendance_records = DailyAttendance.objects.filter(
            student__klass__id=class_id
        ).select_related('student')
        
        results = []
        for record in attendance_records:
            results.append({
                'id': record.id,
                'student': f"{record.student.first_name} {record.student.last_name}",
                'student_id': record.student.id,
                'date': record.date.strftime('%Y-%m-%d'),
                'status': record.status,
                'created': record.created if hasattr(record, 'created') else 'N/A'
            })
        
        return Response({
            'class_id': class_id,
            'total_records': len(results),
            'attendance_records': results
        })
    

    @action(detail=False, methods=['get'])
    def debug_simple(self, request):
        """Simple debug endpoint - no serializers"""
        class_id = request.query_params.get('class_id')
        
        if not class_id:
            return Response({"error": "Please provide class_id parameter"})
        
        # Get all records with dates
        all_records = DailyAttendance.objects.filter(
            student__klass__id=class_id
        ).order_by('date')  # Order by date to see the range
        
        # Get date range info
        dates = all_records.values_list('date', flat=True).distinct()
        date_range = {
            'earliest': min(dates) if dates else None,
            'latest': max(dates) if dates else None,
            'total_dates': len(dates)
        }
        
        # Get sample records
        sample_data = []
        for record in all_records[:10]:  # Show first 10 records
            sample_data.append({
                'student': str(record.student),
                'date': record.date.isoformat(),
                'status': record.status,
                'day_of_week': record.date.strftime('%A')  # Add day name
            })
        
        return Response({
            'message': 'Debug endpoint working',
            'class_id': class_id,
            'total_attendance_records': all_records.count(),
            'date_range': date_range,
            'sample_records': sample_data,
            'all_dates': list(dates) if dates else []  # Show all unique dates
        })







class SchoolCalenderViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolCalenderSerializer
    permission_classes = [IsAuthenticated]
    queryset = SchoolCalender.objects.all()

    @action(detail=False, methods=['post'])
    def set_day(self, request):
        """Set a date as school day or not, and add a note."""
        date = request.data.get('date')
        is_school_day = request.data.get('is_school_day')
        notes = request.data.get('notes', '')
        if not date or is_school_day is None:
            return Response({'error': 'date and is_school_day are required.'}, status=400)
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            is_weekend = date_obj.weekday() in [5, 6]
            # Prevent marking Saturday/Sunday as school day by default, but allow override
            if is_weekend and not is_school_day:
                notes = notes or 'Weekend'
            cal, created = SchoolCalender.objects.get_or_create(date=date)
            cal.is_school_day = is_school_day
            cal.notes = notes
            cal.save()
            return Response(SchoolCalenderSerializer(cal).data)
        except Exception as e:
            return Response({'error': str(e)}, status=400)







