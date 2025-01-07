# attendance/models.py
from django.db import models
from django.utils.timezone import now

class Attendance(models.Model):
    student = models.ForeignKey('authentication.Student', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=now)
    status = models.BooleanField(default=False)  # True = Present, False = Absent

    def __str__(self):
        return f"{self.student.roll_number} - {self.date} - {'Present' if self.status else 'Absent'}"
