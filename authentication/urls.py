from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('counselor_dashboard/', views.counselor_dashboard, name='counselor_dashboard'),
    path('forgot-password/', views.forgotpassword, name='forgotpassword'),
    path('profile/', views.profile_view, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
]
