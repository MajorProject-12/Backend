from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class Student(models.Model):
    GENDER_CHOICES = [
        ('m', 'Male'),
        ('f', 'Female'),
        ('o', 'Other'),
    ]

    SECTION_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    YEAR_CHOICES = [
        (1, 'I'),
        (2, 'II'),
        (3, 'III'),
        (4, 'IV'),
    ]

    SEMESTER_CHOICES = [
        (1, 'I'),
        (2, 'II'),
    ]

    BRANCH_CHOICES = [
        ('CIV', 'Civil Engineering'),
        ('EEE', 'Electrical and Electronics Engineering'),
        ('MEC', 'Mechanical Engineering'),
        ('ECE', 'Electronics and Communication Engineering'),
        ('CSE', 'Computer Science Engineering'),
        ('INF', 'Information Technology'),
        ('CSM', 'Computer Science - Artificial Intelligence and Machine Learning'),
        ('CSO', 'Computer Science - Internet of Things'),
        ('CIC', 'Computer Science - Internet of Things & Cybersecurity'),
        ('AIM', 'Artificial Intelligence and Machine Learning'),
        ('AID', 'Artificial Intelligence and Data Science'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    roll_number = models.CharField(primary_key=True, max_length=20)
    branch = models.CharField(max_length=3, choices=BRANCH_CHOICES)
    year = models.IntegerField(choices=YEAR_CHOICES)
    semester = models.IntegerField(choices=SEMESTER_CHOICES)
    section = models.CharField(max_length=1, choices=SECTION_CHOICES)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    counselor = models.ForeignKey(
        'Counselor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_students'
    )

    def __str__(self):
        return f"{self.user.email} ({self.roll_number}, {self.branch})"


class Counselor(models.Model):
    BRANCH_CHOICES = [
        ('CIV', 'Civil Engineering'),
        ('EEE', 'Electrical and Electronics Engineering'),
        ('MEC', 'Mechanical Engineering'),
        ('ECE', 'Electronics and Communication Engineering'),
        ('CSE', 'Computer Science Engineering'),
        ('INF', 'Information Technology'),
        ('CSM', 'Computer Science - Artificial Intelligence and Machine Learning'),
        ('CSO', 'Computer Science - Internet of Things'),
        ('CIC', 'Computer Science - Internet of Things & Cybersecurity'),
        ('AIM', 'Artificial Intelligence and Machine Learning'),
        ('AID', 'Artificial Intelligence and Data Science'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    branch = models.CharField(max_length=3, choices=BRANCH_CHOICES)

    def __str__(self):
        return f"{self.user.email} ({self.branch})"