# reports/models.py
from django.db import models
from authentication.models import Student, Counselor

class StudentWork(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    # Option 1: Keep auto_now_add=True (simplest)
    # date = models.DateField(auto_now_add=True)
    # Option 2: To allow custom dates, comment out the above line and uncomment the line below
    date = models.DateField()
    work_done = models.TextField()

    def __str__(self):
        return f"{self.student.roll_number} - {self.date}"

class CounselorWork(models.Model):
    counselor = models.ForeignKey(Counselor, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    work_done = models.TextField()

    def __str__(self):
        return f"{self.counselor.user.email} - {self.student.roll_number} - {self.date}"