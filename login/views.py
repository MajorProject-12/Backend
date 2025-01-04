from django.shortcuts import render, redirect

# Welcome Page
def welcome_view(request):
    return render(request, "welcome.html")

# Forgot Password Page
def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        request.session['email'] = email  # Store email in session
        return redirect("verification")
    return render(request, "forgot_password.html")
# Verification Page
def verification_view(request):
    if request.method == "POST":
        verification_code = request.POST.get("verification_code")
        # Add verification logic here...
        return redirect("new_password")
    return render(request, "verification.html")

# New Password Page
def new_password_view(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        if new_password == confirm_password:
            # Update password logic here...
            return redirect("welcome")
    return render(request, "new_password.html")


