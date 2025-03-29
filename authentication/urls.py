# authentication/urls.py

from . import views
from django.urls import path

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgotpassword, name='forgotpassword'),

    # Student URLs - update the URL patterns to match the format
    path('student/check_in/', views.student_check_in, name='student_check_in'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('student/statistics/', views.student_statistics, name='student_statistics'),
    path('student/remarks/', views.student_remarks, name='student_remarks'),
    path('student/leave/', views.student_leave, name='student_leave'),
    path('student/weekly_reports/', views.student_weekly_report, name='student_weekly_reports'),
    path('student/student_DocRAG/', views.student_DocRAG, name='student_DocRAG'),
    path('student/announcements/', views.student_announcements, name='student_announcements'),

    # Counselor URLs
    path('counselor/dashboard/', views.counselor_dashboard, name='counselor_dashboard'),
    path('counselor/insights/', views.student_insights, name='counselor_insights'),
    path('counselor/leave/', views.counselor_leave, name='counselor_leave'),
    path('counselor/leave/update/', views.update_leave_status, name='update_leave_status'),
    path('counselor/leave/filter/', views.filter_leaves, name='filter_leaves'),
    path('counselor/weekly_reports/', views.counselor_weekly_reports, name='counselor_weekly_reports'),
    path("download_attendance/", views.download_attendance, name="download_attendance"),
    path('counselor/attendance/', views.counselor_attendance, name='counselor_attendance'),
    path('counselor/infomate/', views.counselor_chatbot, name='counselor_chatbot'),
    path('counselor/chatbot-response/', views.chatbot_response, name='chatbot_response'),
    path('counselor/announcements/', views.counselor_announcements, name='counselor_announcements'),
]