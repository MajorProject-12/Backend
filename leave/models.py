from django.db import models
from django.utils import timezone
from authentication.models import Student, Counselor


class StudentLeave(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    reason = models.TextField()
    no_of_days = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ], default='Pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.student.roll_number} - {self.date} - {self.status}"

# No CounselorLeave model - simplified system