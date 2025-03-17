# remarks/views.py
from django.shortcuts import render, get_object_or_404, redirect
from authentication.models import Student, Counselor
from attendance.models import Attendance
from remarks.models import CounselorRemark

def counselor_insights(request):
    counselor = get_object_or_404(Counselor, user=request.user)

    # Process remark submission if POST
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        remark_text = request.POST.get("remarks", "").strip()
        if student_id and remark_text:
            student = get_object_or_404(Student, roll_number=student_id)
            attendance = Attendance.objects.filter(student=student).order_by("-date").first()
            latest_percentage = attendance.attendance_percentage if attendance else 0
            CounselorRemark.objects.create(
                counselor=request.user.counselor,
                student=student,
                percentage=latest_percentage,
                remarks=remark_text,
            )
            return redirect("counselor_insights")

    # GET request: List assigned students and their attendance
    students = list(Student.objects.filter(counselor=counselor).prefetch_related("user"))
    student_attendance = {
        student: Attendance.objects.filter(student=student).order_by("-date").first()
        for student in students
    }
    # Annotate each student with latest attendance percentage
    for student in students:
        att = student_attendance.get(student)
        student.latest_attendance = att.attendance_percentage if att else 100

    # Sort: students with lower attendance (especially <70) come first (in increasing order)
    students.sort(key=lambda s: s.latest_attendance)

    search_query = request.GET.get("search", "").strip()
    if search_query:
        students = [s for s in students if
                    search_query.lower() in s.user.first_name.lower() or search_query in s.roll_number]

    context = {
        "students": students,
        "search_query": search_query,
    }
    return render(request, "counselor_insights.html", context)


def student_remarks(request):
    student = get_object_or_404(Student, user=request.user)
    remarks = CounselorRemark.objects.filter(student=student).order_by("-date")
    context = {
        "student": student,
        "remarks": remarks,
    }
    return render(request, "student_remarks.html", context)
