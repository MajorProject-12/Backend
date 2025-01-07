# remarks/models.py
from django.db import models

class Remark(models.Model):
    student = models.ForeignKey('authentication.Student', on_delete=models.CASCADE, related_name='remarks')
    staff = models.ForeignKey('authentication.Counselor', on_delete=models.SET_NULL, null=True,related_name='given_remarks')
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Remark for {self.student.roll_number} by {self.staff.user.username if self.staff else 'Unknown'}"
