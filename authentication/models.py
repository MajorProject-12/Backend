from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(primary_key=True, max_length=20)
    user_mail = models.EmailField()
    branch = models.CharField(max_length=100)
    year = models.IntegerField()
    section = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    counselor = models.ForeignKey('Counselor', on_delete=models.SET_NULL, null=True, related_name='assigned_students')

    def __str__(self):
        return self.user.username


class Counselor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    branch = models.CharField(max_length=100)
    students = models.ManyToManyField(Student, related_name='counselor_groups', blank=True)

    def __str__(self):
        return self.user.username
