# authentication/views.py
from django.contrib.auth import authenticate, login, logout
import random
import string
from authentication.models import CustomUser
from django.conf import settings
from django.utils.text import capfirst
from remarks.models import CounselorRemark
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from reports.models import StudentWork
from leave.models import StudentLeave
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from authentication.models import Counselor
import pandas as pd
from django.http import HttpResponse
from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Student

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
    return render(request, 'mobilenet_student_profile.html', context)

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

    if request.method == "POST":
        date = request.POST.get("date")
        reason = request.POST.get("reason")
        no_of_days = request.POST.get("days")

        # Create leave request
        leave = StudentLeave.objects.create(
            student=student, date=date, reason=reason, no_of_days=no_of_days, status="Pending"
        )

        # Send Email Notification to Counselor with better formatting
        counselor = student.counselor
        counselor_email = counselor.user.email

        # Create a well-structured HTML email
        subject = f"New Leave Application from {student.user.username}"
        html_message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4A90E2; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                .details {{ margin: 15px 0; }}
                .label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>New Leave Application</h2>
                </div>
                <div class="content">
                    <p>Dear {counselor.user.username},</p>

                    <p>A new leave application has been submitted that requires your attention.</p>

                    <div class="details">
                        <p><span class="label">Student Name:</span> {student.user.username}</p>
                        <p><span class="label">Roll Number:</span> {student.roll_number}</p>
                        <p><span class="label">Leave Date:</span> {date}</p>
                        <p><span class="label">Duration:</span> {no_of_days} day{'s' if int(no_of_days) > 1 else ''}</p>
                        <p><span class="label">Reason:</span> {reason}</p>
                    </div>

                    <p>Please review this application at your earliest convenience through the counselor portal.</p>

                    <p>Thank you,<br>
                    Student Management System</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        from email_utils import send_html_email
        send_html_email(
            subject=subject,
            html_message=html_message,
            recipient_list=[counselor_email],
            from_email=settings.DEFAULT_FROM_EMAIL
        )

        messages.success(request, "Leave application submitted successfully!")
        return redirect("student_leave")

    leave_records = StudentLeave.objects.filter(student=student).order_by("-date")
    return render(request, "student_leave.html", {"student": student, "leave_records": leave_records})

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

                # Create the StudentWork instance
                work = StudentWork(
                    student=student,
                    date=date_obj,
                    work_done=work_done
                )

                work.save()

                # Send email notification to counselor
                counselor = student.counselor
                counselor_email = counselor.user.email

                # Format the date for display
                formatted_date = date_obj.strftime('%d %B, %Y')

                # Create HTML email
                subject = f"New Weekly Report from {student.user.username}"
                html_message = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #4A90E2; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                        .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                        .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                        .details {{ margin: 15px 0; background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
                        .label {{ font-weight: bold; }}
                        .work-content {{ white-space: pre-line; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>New Weekly Report Submission</h2>
                        </div>
                        <div class="content">
                            <p>Dear {counselor.user.username},</p>

                            <p>A new weekly report has been submitted by one of your assigned students:</p>

                            <div class="details">
                                <p><span class="label">Student Name:</span> {student.user.username}</p>
                                <p><span class="label">Roll Number:</span> {student.roll_number}</p>
                                <p><span class="label">Report Date:</span> {formatted_date}</p>
                                <p><span class="label">Work Done:</span></p>
                                <div class="work-content">{work_done}</div>
                            </div>

                            <p>You can view all student reports through the counselor portal.</p>

                            <p>Thank you,<br>
                            Student Management System</p>
                        </div>
                        <div class="footer">
                            <p>This is an automated message. Please do not reply to this email.</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                from email_utils import send_html_email
                send_html_email(
                    subject=subject,
                    html_message=html_message,
                    recipient_list=[counselor_email],
                    from_email=settings.DEFAULT_FROM_EMAIL
                )

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

def student_DocRAG(request):
    student = Student.objects.get(user=request.user)
    context = {
        'student': student,
        # 'student_reports': student_reports,
    }
    return render(request, 'student_qabot.html', context)


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

def update_leave_status(request):
    """View to update leave application status"""
    # Check if user is authenticated and is a counselor
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
        return redirect('login')

    # Ensure the user is a counselor
    try:
        counselor = Counselor.objects.get(user=request.user)
    except Counselor.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "message": "Not authorized"}, status=403)
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('dashboard')  # Redirect to appropriate page

    # Get request parameters
    leave_id = request.GET.get('leave_id')
    status = request.GET.get('status')

    # Validate parameters
    if not leave_id or not status or status not in ['Approved', 'Rejected']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "message": "Invalid request"}, status=400)
        messages.error(request, "Invalid request parameters.")
        return redirect('counselor_leave')

    try:
        # Get the leave application
        leave_application = StudentLeave.objects.get(id=leave_id)

        # Check if this counselor is assigned to the student
        if leave_application.student.counselor != counselor:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "message": "Not authorized to update this leave"}, status=403)
            messages.error(request, "You are not authorized to update this leave application.")
            return redirect('counselor_leave')

        # Check if leave is already processed
        if leave_application.status != 'Pending':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "message": "Leave application already processed"}, status=400)
            messages.error(request, "This leave application has already been processed.")
            return redirect('counselor_leave')

        # Update the status
        old_status = leave_application.status
        leave_application.status = status
        leave_application.save()

        # Send email notification to student
        try:
            student = leave_application.student
            student_email = student.user.email

            # Create HTML email based on approval status
            subject = f"Leave Application {status}"

            # Different message content based on status
            if status == 'Approved':
                status_color = '#28a745'  # Green for approved
                status_message = "Your leave application has been approved by your counselor."
                additional_info = "Please make necessary arrangements for any missed classes or assignments."
            else:  # Rejected
                status_color = '#dc3545'  # Red for rejected
                status_message = "Your leave application has been rejected by your counselor."
                additional_info = "If you have any questions about this decision, please contact your counselor directly."

            html_message = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: {status_color}; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                    .details {{ margin: 15px 0; }}
                    .label {{ font-weight: bold; }}
                    .status {{ color: {status_color}; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Leave Application Update</h2>
                    </div>
                    <div class="content">
                        <p>Dear {student.user.username},</p>

                        <p>{status_message}</p>

                        <div class="details">
                            <p><span class="label">Leave Date:</span> {leave_application.date.strftime('%d/%m/%Y')}</p>
                            <p><span class="label">Duration:</span> {leave_application.no_of_days} day{'s' if leave_application.no_of_days > 1 else ''}</p>
                            <p><span class="label">Reason:</span> {leave_application.reason}</p>
                            <p><span class="label">Status:</span> <span class="status">{status}</span></p>
                        </div>

                        <p>{additional_info}</p>

                        <p>Thank you,<br>
                        Student Management System</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            from email_utils import send_html_email
            send_html_email(
                subject=subject,
                html_message=html_message,
                recipient_list=[student_email],
                from_email=settings.DEFAULT_FROM_EMAIL
            )
        except Exception as email_error:
            # Log email error but continue with the response
            print(f"Error sending email notification: {str(email_error)}")

        # Return success response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": True,
                "message": f"Leave application {status.lower()} successfully",
                "leave_id": leave_id,
                "status": status
            })

        messages.success(request, f"Leave application has been {status.lower()} successfully.")
        return redirect('counselor_leave')

    except StudentLeave.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "message": "Leave application not found"}, status=404)
        messages.error(request, "Leave application not found.")
        return redirect('counselor_leave')
    except Exception as e:
        # Log the error
        print(f"Error updating leave status: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "message": "An error occurred"}, status=500)
        messages.error(request, "An error occurred while processing your request.")
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

                # Verify this student is assigned to the current counselor
                if student.counselor == counselor:
                    # Analyze sentiment before creating the remark
                    from .sentiment_utils import analyze_sentiment
                    sentiment_label, confidence_score = analyze_sentiment(remark_text)

                    # Create the remark with sentiment information
                    new_remark = CounselorRemark.objects.create(
                        counselor=counselor,
                        student=student,
                        percentage=student.attendance_percentage,
                        remarks=remark_text,
                        sentiment=sentiment_label,
                        confidence=confidence_score
                    )

                    try:
                        # Send email notification to student
                        student_email = student.user.email

                        # Determine header color based on sentiment
                        if sentiment_label == "NEGATIVE":
                            header_color = '#dc3545'  # Red for negative
                        else:
                            header_color = '#28a745'  # Green for positive

                        # Format the date
                        formatted_date = new_remark.date.strftime('%d %B, %Y')

                        # Create HTML email
                        subject = f"New Counselor Remark from {counselor.user.username}"
                        html_message = f"""
                        <html>
                        <head>
                            <style>
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                                .header {{ background-color: {header_color}; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                                .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                                .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                                .remark {{ margin: 15px 0; background-color: #f9f9f9; padding: 15px; border-radius: 5px; white-space: pre-line; }}
                                .attendance {{ margin-top: 15px; }}
                                .low-attendance {{ color: #dc3545; font-weight: bold; }}
                                .good-attendance {{ color: #28a745; font-weight: bold; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="header">
                                    <h2>New Counselor Remark</h2>
                                </div>
                                <div class="content">
                                    <p>Dear {student.user.username},</p>

                                    <p>Your counselor has provided a new remark regarding your academic progress:</p>

                                    <div class="remark">
                                        "{remark_text}"
                                    </div>

                                    <p><strong>Date:</strong> {formatted_date}</p>

                                    <div class="attendance">
                                        <p><strong>Current Attendance:</strong> 
                                        <span class="{'low-attendance' if student.attendance_percentage < 75 else 'good-attendance'}">
                                            {student.attendance_percentage:.2f}%
                                        </span></p>

                                        {f'<p><strong>Note:</strong> Your attendance is below the required minimum of 75%. Please improve your attendance immediately.</p>' if student.attendance_percentage < 75 else ''}
                                    </div>

                                    <p>You can view all counselor remarks in your student portal.</p>

                                    <p>Best regards,<br>
                                    {counselor.user.username}<br>
                                    Student Counselor</p>
                                </div>
                                <div class="footer">
                                    <p>This is an automated message from the Student Management System.</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        """

                        from email_utils import send_html_email
                        send_html_email(
                            subject=subject,
                            html_message=html_message,
                            recipient_list=[student_email],
                            from_email=settings.DEFAULT_FROM_EMAIL
                        )
                    except Exception as email_error:
                        # Log error but don't prevent remark from being added
                        print(f"Error sending email notification: {str(email_error)}")

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

@login_required
def download_attendance(request):
    counselor = request.user.counselor
    students = Student.objects.filter(counselor=counselor).select_related("user")

    if not students.exists():
        messages.info(request, "No students assigned to you.")
        return redirect("counselor_insights")

    # Prepare data for the Excel file
    data = []
    for student in students:
        # first_name = student.user.first_name if student.user and student.user.first_name else ""
        # last_name = student.user.last_name if student.user and student.user.last_name else ""
        full_name = student.user.username if student.user and student.user.username else ""
        # full_name = f"{first_name} {last_name}".strip()

        data.append([
            student.roll_number,
            full_name,  # Ensure it's never None
            round(student.attendance_percentage, 2),
        ])

    # Create a Pandas DataFrame
    df = pd.DataFrame(data, columns=["Roll Number", "Student Name", "Attendance (%)"])

    # Save DataFrame to an Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Attendance", index=False)
        writer.close()

    # Set response headers for file download
    response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="Student_Attendance.xlsx"'
    return response

# def counselor_attendance(request):

