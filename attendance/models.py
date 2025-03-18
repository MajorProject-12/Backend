# attendance/models.py
from django.db import models
from django.utils import timezone

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    ]

    student = models.ForeignKey("authentication.Student", on_delete=models.CASCADE)  # ✅ Lazy import
    date = models.DateField(default=timezone.now)
    time = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')

    def __str__(self):
        return f"{self.student.roll_number} - {self.date} - {self.status}"

    class Meta:
        unique_together = ('student', 'date')  # ✅ Ensures attendance is marked only once per student per day


class FaceRegistration(models.Model):
    student = models.OneToOneField("authentication.Student", on_delete=models.CASCADE)  # ✅ Lazy import
    face_features = models.BinaryField(null=True, blank=True)  
    face_image = models.ImageField(upload_to='face_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.student.roll_number}'s Face Registration"