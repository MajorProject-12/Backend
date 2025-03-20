from django.urls import path
from . import views

urlpatterns = [
    # Student URLs
    path('student/weekly-reports/', views.student_weekly_reports, name='student_weekly_reports'),

    # Counselor URLs
    path('counselor/weekly-reports/', views.counselor_weekly_reports, name='counselor_weekly_reports'),
    path('counselor/search-reports/', views.search_reports, name='search_reports'),
]