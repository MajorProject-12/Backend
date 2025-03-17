from django.contrib import admin
from .models import Attendance, FaceRegistration

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'student_attendance_percentage')
    list_filter = ('status', 'date')
    search_fields = ('student__roll_number', 'student__user__first_name', 'student__user__last_name')

    def student_attendance_percentage(self, obj):
        return f"{obj.student.attendance_percentage:.2f}%"  # ✅ Display attendance percentage
    student_attendance_percentage.short_description = "Attendance (%)"


@admin.register(FaceRegistration)
class FaceRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student',)
    search_fields = ('student__roll_number', 'student__user__first_name', 'student__user__last_name')
