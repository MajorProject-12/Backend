# attendance/models.py

from django.db import models
from authentication.models import Student
from remarks.models import CounselorRemark
from django.utils import timezone

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    time = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')
    attendance_percentage = models.FloatField(null=True, blank=True)

    def update_percentage(self):
        # Fetch the latest remark entry for the student and update attendance percentage
        latest_remark = CounselorRemark.objects.filter(student=self.student).order_by('-date').first()
        if latest_remark:
            self.attendance_percentage = latest_remark.percentage
            self.save()

    def __str__(self):
        return f"{self.student.roll_number} - {self.date} - {self.status} ({self.attendance_percentage}%)"

    class Meta:
        unique_together = ('student', 'date')  # Ensure attendance is marked only once per day per student
