# attendance_statistics/models.py

from django.db import models
from authentication.models import Student

class AttendanceStatistics(models.Model):
    """
    Stores attendance statistics for a particular student in a specific semester/year.
    Links to the Student model so you can retrieve user info easily.
    """

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_statistics'
    )

    # If you track by semester and year:
    year = models.IntegerField(
        choices=Student.YEAR_CHOICES,
        null=True,
        blank=True
    )
    semester = models.IntegerField(
        choices=Student.SEMESTER_CHOICES,
        null=True,
        blank=True
    )

    working_days = models.IntegerField(default=0)
    public_holidays = models.IntegerField(default=0)
    present_percentage = models.FloatField(default=0.0)
    absent_percentage = models.FloatField(default=0.0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Stats for {self.student.roll_number} "
            f"(Year {self.year}, Sem {self.semester}) - "
            f"Present: {self.present_percentage}%, Absent: {self.absent_percentage}%"
        )
