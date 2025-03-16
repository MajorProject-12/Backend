# leave/models.py
from django.db import models
from authentication.models import Student, Counselor

class StudentLeave(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    reason = models.TextField()
    no_of_days = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')])

    def __str__(self):
        return f"{self.student.roll_number} - {self.date} - {self.status}"

class CounselorLeave(models.Model):
    counselor = models.ForeignKey(Counselor, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')])

    def __str__(self):
        return f"{self.counselor.user.email} - {self.student.roll_number} - {self.status}"
