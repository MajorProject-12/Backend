# remarks/models.py
from django.db import models

class StudentRemark(models.Model):
    student = models.ForeignKey("authentication.Student", on_delete=models.CASCADE)  # ✅ Lazy import
    date = models.DateField(auto_now_add=True)
    remarks = models.TextField()

    def __str__(self):
        return f"Remark for {self.student.roll_number} on {self.date}"


class CounselorRemark(models.Model):
    counselor = models.ForeignKey("authentication.Counselor", on_delete=models.CASCADE)  # ✅ Lazy import
    student = models.ForeignKey("authentication.Student", on_delete=models.CASCADE)  # ✅ Lazy import
    date = models.DateField(auto_now_add=True)
    percentage = models.FloatField()
    remarks = models.TextField()

    def __str__(self):
        return f"Remark by {self.counselor.user.email} for {self.student.roll_number} on {self.date}"
