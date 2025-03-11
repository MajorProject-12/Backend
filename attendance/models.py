# attendance/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import pickle

class FaceRegistration(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    face_features = models.BinaryField(null=True, blank=True)
    face_image = models.ImageField(upload_to='face_images/', null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save_features(self, features):
        self.face_features = pickle.dumps(features)
        self.save()

    def get_features(self):
        if self.face_features:
            return pickle.loads(self.face_features)
        return None

    def __str__(self):
        return f"{self.user.email}'s Face Registration"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    student = models.ForeignKey('authentication.Student', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    time = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')
    verified_by = models.CharField(max_length=20, default='Face Recognition')

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.student.roll_number} - {self.date} - {self.status}"