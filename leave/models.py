# leave/models.py
from django.db import models

class LeaveApplication(models.Model):
    student = models.ForeignKey('authentication.Student', on_delete=models.CASCADE, related_name='leave_applications')
    date_applied = models.DateField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')

    def __str__(self):
        return f"{self.student.roll_number} - {self.status}"
