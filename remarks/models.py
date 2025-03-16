# remarks/models.py
from django.db import models
from authentication.models import Student, Counselor

class StudentRemark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    remarks = models.TextField()

    def __str__(self):
        return f"Remark for {self.student.roll_number} on {self.date}"


class CounselorRemark(models.Model):
    counselor = models.ForeignKey(Counselor, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    percentage = models.FloatField()  # Attendance percentage assigned by the counselor
    remarks = models.TextField()

    def __str__(self):
        return f"Remark by {self.counselor.user.email} for {self.student.roll_number} on {self.date}"

    def save(self, *args, **kwargs):
        """Update the student's attendance percentage when a new remark is added."""
        super().save(*args, **kwargs)  # Save the remark first

        # Update the latest attendance record's percentage
        attendance_record = self.student.attendance_set.filter(date=self.date).first()
        if attendance_record:
            attendance_record.attendance_percentage = self.percentage
            attendance_record.save()
