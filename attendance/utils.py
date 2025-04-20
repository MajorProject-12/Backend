# attendance/utils.py

from .models import Attendance

# ERP‐mandated instruction days per semester (JNTU‑K, R23/R20/R19 all specify ≥ 90 days)
SEMESTER_INSTRUCTION_DAYS = {sem: 90 for sem in range(1, 9)}

def update_attendance_percentage(student, is_present: bool):
    """
    Incrementally update a student's attendance % per JNTU‑K ERP:
      1. Converts old % back to present‐days count.
      2. Adds today’s present (1) or absent (0).
      3. Calculates new % = (new_present_days / 90) * 100.
    """
    # Total instruction days for this semester
    total_days = SEMESTER_INSTRUCTION_DAYS.get(student.semester, 90)
    # Derive previous present‑day count from stored percentage
    prev_present = int(round(student.attendance_percentage / 100 * total_days))
    # Increment if today was marked present
    new_present = prev_present + (1 if is_present else 0)
    # Compute updated percentage
    percentage = round((new_present / total_days) * 100, 2)
    # Persist change
    student.attendance_percentage = percentage
    student.save()
