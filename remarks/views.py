# remarks/views.py
from django.shortcuts import render, get_object_or_404, redirect
from authentication.models import Student, Counselor
from attendance.models import Attendance
from remarks.models import CounselorRemark
from django.contrib import messages

def counselor_insights(request):
    # Get the counselor object for the current user
    counselor = get_object_or_404(Counselor, user=request.user)

    # Process remark submission if POST
    if request.method == "POST":
        student_roll = request.POST.get("student_id")
        remark_text = request.POST.get("remarks", "").strip()

        if student_roll and remark_text:
            try:
                student = Student.objects.get(roll_number=student_roll)

                # Debug information
                print(f"Creating remark for {student_roll}: {remark_text}")
                print(f"Student found: {student}")
                print(f"Counselor: {counselor}")

                # Verify this student is assigned to the current counselor
                if student.counselor == counselor:
                    # Create the remark
                    new_remark = CounselorRemark.objects.create(
                        counselor=counselor,
                        student=student,
                        percentage=student.attendance_percentage,
                        remarks=remark_text,
                    )
                    print(f"Remark created: {new_remark}")
                    messages.success(request, "Remark added successfully!")
                    return redirect("counselor_insights")
                else:
                    # Handle case where student doesn't belong to this counselor
                    messages.error(request, "You can only add remarks for your assigned students.")
            except Student.DoesNotExist:
                messages.error(request, f"Student with roll number {student_roll} not found")

    # GET request: List assigned students and their attendance
    students = Student.objects.filter(counselor=counselor).select_related("user")

    # Make sure we have students to display
    if not students.exists():
        messages.info(request, "No students are currently assigned to you.")

    # For each student, use their attendance_percentage field for display in the template
    for student in students:
        # Format attendance percentage for display (round to 2 decimal places)
        student.latest_attendance = round(student.attendance_percentage, 2)
        # Debug student information
        print(f"Student: {student.roll_number}, User: {student.user.first_name} {student.user.last_name}")

    # Sort students: lower attendance come first
    students = sorted(students, key=lambda s: s.latest_attendance)

    # Server-side search filtering
    search_query = request.GET.get("search", "")
    if search_query:
        filtered_students = []
        for student in students:
            full_name = f"{student.user.first_name} {student.user.last_name}".lower()
            if (search_query.lower() in full_name or
                    search_query.lower() in student.roll_number.lower()):
                filtered_students.append(student)
        students = filtered_students

    context = {
        "counselor": counselor,
        "students": students,
        "search_query": search_query,
    }
    return render(request, "counselor_insights.html", context)


def student_remarks(request):
    student = get_object_or_404(Student, user=request.user)
    remarks = CounselorRemark.objects.filter(student=student).order_by("-date")

    # Debug info
    print(f"Student: {student.roll_number}")
    print(f"Remarks count: {remarks.count()}")
    for remark in remarks:
        print(f"Remark date: {remark.date}, text: {remark.remarks}")

    if not remarks.exists():
        messages.info(request, "No counselor remarks available yet.")

    context = {
        "student": student,
        "remarks": remarks,
    }
    return render(request, "student_remarks.html", context)