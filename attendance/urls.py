# In your urls.py file, ensure these routes are properly defined:

from django.urls import path
from . import views

urlpatterns = [
    # ... other URL patterns

    # Profile and face registration
    # path('profile/', views.profile_view, name='profile'),
    path('check_registration/', views.check_registration, name='check_registration'),
    path('register_face/', views.register_face, name='register_face'),

    # Check-in and attendance
    path('student_check_in/', views.student_check_in, name='student_check_in'),
    path('mark_attendance/', views.mark_attendance, name='mark_attendance'),

    # ... other URL patterns
]