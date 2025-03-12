from tkinter.font import names

from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgotpassword, name='forgotpassword'),

    # Student URLs
    path('student_check_in/', views.student_check_in, name='student_check_in'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('student_statistics/', views.student_statistics, name='student_statistics'),
    path('student_remarks/', views.student_remarks, name='student_remarks'),
    path('student_leave/', views.student_leave, name='student_leave'),
    path('student_weekly_reports/', views.student_weekly_report, name='student_weekly_reports'),

    # Counselor URLs
    path('counselor_dashboard/', views.counselor_dashboard, name='counselor_dashboard'),
    path('student_insights/', views.student_insights, name='student_insights'),
    path('counselor_leave/', views.counselor_leave, name='counselor_leave'),
    path('counselor_weekly_reports/', views.counselor_weekly_reports, name='counselor_weekly_reports'),

]
