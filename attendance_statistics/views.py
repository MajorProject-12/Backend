# attendance_statistics/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from attendance_statistics.models import AttendanceStatistics

@login_required
def student_statistics_view(request):
    # Get the logged-in student
    student = request.user.student

    # Retrieve the latest attendance statistics record for this student
    stats = student.attendance_statistics.order_by('-updated_at').first()

    # Build the context; stats may be None if no record exists
    context = {
        'student': student,
        'stats': stats,
    }
    return render(request, 'student_statistics.html', context)
