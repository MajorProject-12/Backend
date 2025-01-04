from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome_view, name="welcome"),
    path('forgot-password/', views.forgot_password_view, name="forgot_password"),
    path('verification/', views.verification_view, name="verification"),
    path('new-password/', views.new_password_view, name="new_password"),
]
