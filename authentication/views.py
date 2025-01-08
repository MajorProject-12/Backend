from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime, timedelta


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
        'courses': [],  # Add your course data here
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