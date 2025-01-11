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

                # Handle remember me
                if remember_me:
                    # Set session expiry to 30 days
                    request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days in seconds
                else:
                    # Set session expiry to 0 (until browser closes)
                    request.session.set_expiry(0)

                messages.success(request, "Login successful! Welcome, Student.")
                return redirect('student_dashboard')

            elif role == 'Counselor' and hasattr(user, 'counselor'):
                login(request, user)

                # Handle remember me
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
def student_dashboard(request):
    student = request.user.student
    context = {
        'student': student,
        'courses': [],
    }
    return render(request, 'student_dashboard.html', context)


@login_required
def counselor_dashboard(request):
    counselor = request.user.counselor
    context = {
        'counselor': counselor,
        'assigned_students': counselor.assigned_students.all(),
    }
    return render(request, 'counselor_dashboard.html', context)


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
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
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
                    # Update the stage to 'otp'
                    request.session['stage'] = 'otp'
                    current_stage = 'otp'  # Update current stage
                    messages.success(request, 'OTP has been sent to your email.')
                else:
                    messages.error(request, 'Failed to send OTP. Please try again.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'No account found with this email address.')

        elif 'otp' in request.POST:
            user_otp = request.POST['otp']
            stored_otp = request.session.get('otp')

            if stored_otp and user_otp == stored_otp:
                # Update stage to password
                request.session['stage'] = 'password'
                current_stage = 'password'  # Update current stage
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
                    # Clear session data
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
            # Update user fields
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.save()

            # Update student fields
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