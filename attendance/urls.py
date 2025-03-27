# In your urls.py file

from django.urls import path
from . import views, mobilenet_views

urlpatterns = [
    # Profile and face registration
    # path('profile/', views.profile_view, name='profile'),
    path('check_registration/', views.check_registration, name='check_registration'),
    path('register_face/', views.register_face, name='register_face'),

    # Check-in and attendance
    path('student_check_in/', views.student_check_in, name='student_check_in'),
    path('mark_attendance/', views.mark_attendance, name='mark_attendance'),

    # New streaming endpoints
    path('receive_video_frame/', views.receive_video_frame, name='receive_video_frame'),
    path('start_attendance_verification/', views.start_attendance_verification, name='start_attendance_verification'),
    path('stop_video_stream/', views.stop_video_stream, name='stop_video_stream'),

    path('mobilenet/profile/', mobilenet_views.mobilenet_profile, name='mobilenet_profile'),
    path('mobilenet/check_registration/', mobilenet_views.mobilenet_check_registration, name='mobilenet_check_registration'),
    path('mobilenet/register_face/', mobilenet_views.mobilenet_register_face, name='mobilenet_register_face'),
    path('mobilenet/recognize/', mobilenet_views.mobilenet_recognize, name='mobilenet_recognize'),
]