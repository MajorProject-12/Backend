from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Attendance
from authentication.models import Student

# @receiver([post_save, post_delete], sender=Attendance)
# def update_student_attendance(sender, instance, **kwargs):
#     student = instance.student
#     total_attendance = Attendance.objects.filter(student=student).count()
#     present_days = Attendance.objects.filter(student=student, status='Present').count()
#
#     if total_attendance > 0:
#         student.attendance_percentage = (present_days / total_attendance) * 100
#     else:
#         student.attendance_percentage = 0.0
#
#     student.save(update_fields=['attendance_percentage'])  # ✅ Efficient update


from remarks.models import CounselorRemark


@receiver([post_save, post_delete], sender=Attendance)
def update_student_attendance(sender, instance, **kwargs):
    student = instance.student
    total_attendance = Attendance.objects.filter(student=student).count()
    present_days = Attendance.objects.filter(student=student, status='Present').count()

    percentage = 0.0
    if total_attendance > 0:
        percentage = (present_days / total_attendance) * 100

    # Find the latest CounselorRemark for this student
    latest_remark = CounselorRemark.objects.filter(student=student).order_by('-date').first()

    if latest_remark:
        latest_remark.percentage = percentage
        # Use update() to avoid triggering signals
        CounselorRemark.objects.filter(id=latest_remark.id).update(percentage=percentage)