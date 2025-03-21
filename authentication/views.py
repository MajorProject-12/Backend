# authentication/views.py
from django.contrib.auth import authenticate, login, logout
import random
import string
from django.shortcuts import render, redirect
from authentication.models import CustomUser
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.text import capfirst
from django.contrib import messages
from django.shortcuts import get_object_or_404
from remarks.models import CounselorRemark
from authentication.models import Student, Counselor
from attendance.models import Attendance
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from reports.models import StudentWork, CounselorWork
from leave.models import StudentLeave

#############################################################
#                   Student Views                           #
#############################################################

def login_view(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember') == 'on'

        # Authenticate user with email
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Check role and redirect based on it
            if role == 'Student' and hasattr(user, 'student'):
                login(request, user)
                if remember_me:
                    request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days
                else:
                    request.session.set_expiry(0)
                messages.success(request, "Login successful! Welcome, Student.")
                return redirect('student_dashboard')

            elif role == 'Counselor' and hasattr(user, 'counselor'):
                login(request, user)
                if remember_me:
                    request.session.set_expiry(30 * 24 * 60 * 60)
                else:
                    request.session.set_expiry(0)
                messages.success(request, "Login successful! Welcome, Counselor.")
                return redirect('counselor_dashboard')

            else:
                messages.error(request, "Invalid role selected for your account.")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'index.html')


@login_required
def student_check_in(request):
    student = request.user.student
    context = {
        'student': student,
    }
    return render(request, 'student_check_in.html', context)


@login_required
def student_dashboard(request):
    student = request.user.student
    context = {
        'student': student,
        # 'courses': [],  # Uncomment if courses are used
    }
    return render(request, 'student_dashboard.html', context)


def logout_view(request):
    request.session.flush()
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(email, otp):
    """Send OTP via email"""
    subject = 'Password Reset OTP'
    message = f'Your OTP for password reset is: {otp}\nThis OTP is valid for a limited time.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def forgotpassword(request):
    # Get current stage from session, default to 'email'
    current_stage = request.session.get('stage', 'email')

    if request.method == 'POST':
        if 'email' in request.POST:
            email = request.POST['email']
            try:
                user = CustomUser.objects.get(email=email)
                otp = generate_otp()
                if send_otp_email(email, otp):
                    # Store the OTP and email in session
                    request.session['otp'] = otp
                    request.session['email'] = email
                    request.session['stage'] = 'otp'
                    current_stage = 'otp'
                    messages.success(request, 'OTP has been sent to your email.')
                else:
                    messages.error(request, 'Failed to send OTP. Please try again.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'No account found with this email address.')

        elif 'otp' in request.POST:
            user_otp = request.POST['otp']
            stored_otp = request.session.get('otp')

            if stored_otp and user_otp == stored_otp:
                request.session['stage'] = 'password'
                current_stage = 'password'
                messages.success(request, 'OTP verified successfully. Please enter your new password.')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')

        elif 'new_password1' in request.POST and 'new_password2' in request.POST:
            new_password1 = request.POST['new_password1']
            new_password2 = request.POST['new_password2']
            email = request.session.get('email')

            if new_password1 == new_password2:
                try:
                    user = CustomUser.objects.get(email=email)
                    user.set_password(new_password1)
                    user.save()
                    request.session.flush()
                    messages.success(request, 'Password changed successfully. Please login with your new password.')
                    return redirect('login')
                except CustomUser.DoesNotExist:
                    messages.error(request, 'An error occurred. Please try again.')
            else:
                messages.error(request, 'Passwords do not match. Please try again.')
    else:
        # For GET requests, reset to email stage
        request.session['stage'] = 'email'
        current_stage = 'email'

    return render(request, 'forget_password.html', {'stage': current_stage})


@login_required
def profile_view(request):
    try:
        student = request.user.student

        # Get display values for choice fields
        gender_display = dict(student.GENDER_CHOICES).get(student.gender, '')
        branch_display = dict(student.BRANCH_CHOICES).get(student.branch, '')
        year_display = dict(student.YEAR_CHOICES).get(student.year, '')
        semester_display = dict(student.SEMESTER_CHOICES).get(student.semester, '')
        section_display = dict(student.SECTION_CHOICES).get(student.section, '')

        context = {
            'student': student,
            'user': request.user,
            'gender_display': capfirst(gender_display),
            'branch_display': branch_display,
            'year_display': year_display,
            'semester_display': semester_display,
            'section_display': section_display,
        }

        return render(request, 'student_profile.html', context)

    except Exception as e:
        messages.error(request, "Error loading profile data.")
        return render(request, 'student_profile.html', {'error': str(e)})


@login_required
def update_profile(request):
    if request.method == 'POST':
        student = request.user.student
        user = request.user

        try:
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.save()
            student.branch = request.POST.get('branch')
            student.year = int(request.POST.get('year'))
            student.semester = int(request.POST.get('semester'))
            student.gender = request.POST.get('gender')
            student.save()
            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
        return redirect('profile')
    return redirect('profile')


@login_required
def student_statistics(request):
    student = getattr(request.user, 'student', None)
    if student is None:
        messages.error(request, "Student data not found.")
        return redirect('student_dashboard')
    context = {'student': student}
    return render(request, 'student_statistics.html', context)

@login_required
def student_remarks(request):
    # Get the current student
    student = get_object_or_404(Student, user=request.user)
    # Get all remarks for this student, ordered by most recent first
    remarks = CounselorRemark.objects.filter(student=student).order_by("-date")
    # Debug info
    print(f"Current user ID: {request.user.id}, Username: {request.user.username}")
    print(f"Student: {student.roll_number}")
    print(f"Remarks count: {remarks.count()}")
    for remark in remarks:
        print(f"Remark date: {remark.date}, text: {remark.remarks}")

    # Message if no remarks
    if not remarks.exists():
        messages.info(request, "No counselor remarks available yet.")

    # Setup context for the template
    context = {
        "student": student,
        "remarks": remarks,
    }
    # Render the template
    return render(request, "student_remarks.html", context)

@login_required
def student_leave(request):
    """View for student leave application page"""
    student = get_object_or_404(Student, user=request.user)

    if request.method == 'POST':
        date = request.POST.get('date')
        reason = request.POST.get('reason')
        no_of_days = request.POST.get('days')

        # Create new leave application with Pending status
        leave = StudentLeave.objects.create(
            student=student,
            date=date,
            reason=reason,
            no_of_days=no_of_days,
            status='Pending'
        )

        messages.success(request, "Leave application submitted successfully!")
        return redirect('student_leave')

    # Get all leave applications for this student - force database refresh
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")  # Force connection refresh

    # Query again with fresh connection
    leave_records = StudentLeave.objects.filter(student=student).order_by('-date')

    # Add debug output
    print(f"Retrieved {leave_records.count()} leave records for student {student.roll_number}")
    for record in leave_records:
        print(f"Leave record - ID: {record.id}, Date: {record.date}, Status: {record.status}")

    context = {
        'student': student,
        'leave_records': leave_records
    }

    return render(request, 'student_leave.html', context)

@login_required
def student_weekly_report(request):
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

#############################################################
#                  Counselor Views                          #
#############################################################

@login_required
def counselor_dashboard(request):
    counselor = request.user.counselor
    context = {
        'counselor': counselor,
        'assigned_students': counselor.assigned_students.all(),
    }
    return render(request, 'counselor_dashboard.html', context)


@login_required
def student_insights(request):
    # Get the counselor object for the current user
    counselor = get_object_or_404(Counselor, user=request.user)

    # Process remark submission if POST
    if request.method == "POST":
        student_roll = request.POST.get("student_id")
        remark_text = request.POST.get("remarks", "").strip()

        if student_roll and remark_text:
            try:
                student = Student.objects.get(roll_number=student_roll)

                # # Debug information
                # print(f"Creating remark for {student_roll}: {remark_text}")
                # print(f"Student found: {student}")
                # print(f"Counselor: {counselor}")

                # Verify this student is assigned to the current counselor
                if student.counselor == counselor:
                    # Create the remark
                    new_remark = CounselorRemark.objects.create(
                        counselor=counselor,
                        student=student,
                        percentage=student.attendance_percentage,
                        remarks=remark_text,
                    )
                    # print(f"Remark created: {new_remark}")
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
        # print(f"Student: {student.roll_number}, User: {student.user.first_name} {student.user.last_name}")

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


@login_required
def counselor_leave(request):
    """View for counselor leave application page - improved to show pending requests in 'New' tab"""
    counselor = get_object_or_404(Counselor, user=request.user)

    # Get all students assigned to this counselor
    students = Student.objects.filter(counselor=counselor)

    # Get pending leave applications for the New tab
    pending_leaves = StudentLeave.objects.filter(
        student__in=students,
        status='Pending'
    ).order_by('-created_at')  # Most recent first

    # Get all non-pending leave applications for the Records tab
    processed_leaves = StudentLeave.objects.filter(
        student__in=students
    ).exclude(
        status='Pending'
    ).order_by('-created_at')  # Most recent first

    print(f"Found {pending_leaves.count()} pending leave applications")
    print(f"Found {processed_leaves.count()} processed leave applications")

    context = {
        'counselor': counselor,
        'today_leaves': pending_leaves,
        # Renamed from 'today_leaves' but keeping the variable for template compatibility
        'all_leaves': processed_leaves,
    }

    return render(request, 'counselor_leave.html', context)


@login_required
def update_leave_status(request):
    """
    Simplified view to handle leave status updates.
    No Reset functionality - only approving or rejecting is allowed.
    """
    print("===== UPDATE LEAVE STATUS VIEW CALLED =====")
    print(f"Request method: {request.method}")

    # Get parameters from either GET or POST
    if request.method == 'GET':
        leave_id = request.GET.get('leave_id')
        new_status = request.GET.get('status')
    elif request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        new_status = request.POST.get('status')
    else:
        messages.error(request, "Invalid request method")
        return redirect('counselor_leave')

    print(f"Parameters: leave_id={leave_id}, new_status={new_status}")

    # Validate the parameters
    if not leave_id or not new_status:
        messages.error(request, "Missing required parameters")
        return redirect('counselor_leave')

    # Only allow Approved or Rejected status changes (no Reset to Pending)
    if new_status not in ['Approved', 'Rejected']:
        messages.error(request, "Invalid status value")
        return redirect('counselor_leave')

    try:
        # Get the leave record
        leave = StudentLeave.objects.get(id=leave_id)
        print(f"Found leave record: {leave}")

        # Get the counselor
        counselor = get_object_or_404(Counselor, user=request.user)
        print(f"Found counselor: {counselor}")

        # Security check - ensure counselor is allowed to update this leave
        if leave.student.counselor != counselor:
            messages.error(request, "You are not authorized to update this leave application")
            return redirect('counselor_leave')

        # Ensure the leave is in Pending status before allowing changes
        if leave.status != 'Pending':
            messages.error(request, "Only pending leave applications can be updated")
            return redirect('counselor_leave')

        # Record old status for messaging
        old_status = leave.status

        # Update the leave status
        leave.status = new_status
        leave.save()

        # Verify the update was successful by refreshing from DB
        leave.refresh_from_db()

        if leave.status != new_status:
            print(f"WARNING: Status update failed - DB still shows {leave.status} instead of {new_status}")
            messages.error(request, "Status update failed - please try again")
        else:
            print(f"Successfully updated leave status from {old_status} to {new_status}")

            # Customize message based on the action taken
            if new_status == 'Approved':
                messages.success(request, f"Leave application for {leave.student.roll_number} has been approved")
            elif new_status == 'Rejected':
                messages.success(request, f"Leave application for {leave.student.roll_number} has been rejected")

    except StudentLeave.DoesNotExist:
        print(f"Error: Leave record with ID {leave_id} not found")
        messages.error(request, "Leave application not found")
    except Exception as e:
        print(f"Error updating leave status: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        messages.error(request, f"Error updating leave status: {str(e)}")

    return redirect('counselor_leave')

@login_required
def filter_leaves(request):
    """Filter leave records by search term, month, or year"""
    if request.method == 'GET':
        search_term = request.GET.get('search', '')
        month = request.GET.get('month', '')
        year = request.GET.get('year', '')

        counselor = get_object_or_404(Counselor, user=request.user)
        students = Student.objects.filter(counselor=counselor)

        # Get pending leaves (for New tab)
        pending_leaves = StudentLeave.objects.filter(
            student__in=students,
            status='Pending'
        )

        # Start with all processed leaves (non-pending) for Records tab
        processed_leaves = StudentLeave.objects.filter(
            student__in=students
        ).exclude(
            status='Pending'
        )

        # Apply search term filter to processed leaves if provided
        if search_term:
            processed_leaves = processed_leaves.filter(
                Q(student__user__username__icontains=search_term) |
                Q(student__roll_number__icontains=search_term)
            )

        # Apply date filters if provided
        if month and month != 'Select':
            processed_leaves = processed_leaves.filter(date__month=month)
        if year and year != 'Select':
            processed_leaves = processed_leaves.filter(date__year=year)

        # Order the results by most recent first
        pending_leaves = pending_leaves.order_by('-created_at')
        processed_leaves = processed_leaves.order_by('-created_at')

        context = {
            'counselor': counselor,
            'today_leaves': pending_leaves,  # Keep the variable name for template compatibility
            'all_leaves': processed_leaves,
            'search_term': search_term,
            'month': month,
            'year': year
        }

        return render(request, 'counselor_leave.html', context)

    return redirect('counselor_leave')

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

# Add the search_reports view as well
@login_required
def search_reports(request):
    """API view for searching student reports"""
    try:
        counselor = Counselor.objects.get(user=request.user)
    except Counselor.DoesNotExist:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    # Get search parameters
    search_query = request.GET.get('query', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')

    # Get students assigned to this counselor
    students = Student.objects.filter(counselor=counselor)

    # Start with all reports
    reports = StudentWork.objects.filter(student__in=students)

    # Apply search filters
    if search_query:
        reports = reports.filter(
            Q(student__roll_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query)
        )

    # Apply date filters
    if month and month != 'Select':
        reports = reports.filter(date__month=int(month))

    if year and year != 'Select':
        reports = reports.filter(date__year=int(year))

    # Convert to list of dictionaries for JSON response
    reports_data = []
    for i, report in enumerate(reports.order_by('-date'), 1):
        reports_data.append({
            'sno': i,
            'date': report.date.strftime('%d/%m/%Y'),
            'roll_no': report.student.roll_number,
            'student_name': f"{report.student.user.first_name} {report.student.user.last_name}",
            'work_done': report.work_done,
        })

    return JsonResponse({'reports': reports_data})