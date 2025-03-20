# leave/models.py
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
    ])
    created_at = models.DateTimeField(default=timezone.now)  # Use default instead of auto_now_add

    def __str__(self):
        return f"{self.student.roll_number} - {self.date} - {self.status}"

class CounselorLeave(models.Model):
    counselor = models.ForeignKey(Counselor, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ])
    updated_at = models.DateTimeField(default=timezone.now)  # Use default instead of auto_now

    def __str__(self):
        return f"{self.counselor.user.email} - {self.student.roll_number} - {self.status}"

    def save(self, *args, **kwargs):
        # Update timestamp when saving
        if self.pk:  # If record exists
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)