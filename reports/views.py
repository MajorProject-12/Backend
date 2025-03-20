# reports/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse, NoReverseMatch
from datetime import datetime, timedelta
from authentication.models import Student, Counselor
from .models import StudentWork, CounselorWork

# Student views
@login_required
def student_weekly_reports(request):
    """View for students to submit weekly reports and view their report history"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "You don't have a student profile.")
        return redirect('dashboard')

    if request.method == 'POST':
        date_str = request.POST.get('date')
        work_done = request.POST.get('work_done')

        if date_str and work_done:
            try:
                # Parse the date string into a date object
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                # Create the StudentWork instance directly
                work = StudentWork(
                    student=student,
                    date=date_obj,  # Set the date value
                    work_done=work_done
                )

                work.save()
                messages.success(request, "Weekly report submitted successfully.")
                return redirect('student_weekly_reports')
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD format.")
            except Exception as e:
                messages.error(request, f"Error saving report: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")

    # Get student's reports history
    student_reports = StudentWork.objects.filter(student=student).order_by('-date')

    context = {
        'student': student,
        'student_reports': student_reports,
    }

    return render(request, 'student_weekly_reports.html', context)


@login_required
def counselor_weekly_reports(request):
    """View for counselors to view student reports"""
    try:
        counselor = Counselor.objects.get(user=request.user)
    except Counselor.DoesNotExist:
        messages.error(request, "You don't have a counselor profile.")
        return redirect('dashboard')

    # Get this week's reports (from last Monday to now)
    today = timezone.now().date()
    last_monday = today - timedelta(days=today.weekday())  # Get the most recent Monday

    # Get students assigned to this counselor
    students = Student.objects.filter(counselor=counselor)

    # Get this week's reports for the counselor's students
    this_week_reports = StudentWork.objects.filter(
        student__in=students,
        date__gte=last_monday
    ).order_by('-date')

    # Get all reports for archive
    all_reports = StudentWork.objects.filter(
        student__in=students
    ).order_by('-date')

    context = {
        'counselor': counselor,
        'this_week_reports': this_week_reports,
        'all_reports': all_reports,
        'searchApiUrl': '/counselor/search-reports/',  # Direct URL instead of using reverse()
    }
    return render(request, 'counselor_weekly_reports.html', context)