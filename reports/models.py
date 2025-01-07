# reports/models.py
from django.db import models

class AttendanceReport(models.Model):
    generated_on = models.DateTimeField(auto_now_add=True)
    branch = models.CharField(max_length=50)
    section = models.CharField(max_length=5)
    report_file = models.FileField(upload_to='reports/')

    def __str__(self):
        return f"Report for {self.branch}-{self.section} on {self.generated_on}"
