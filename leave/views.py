# # leave/views.py
# from django.shortcuts import render, redirect, get_object_or_404
# from django.http import JsonResponse
# from django.utils import timezone
# from datetime import timedelta
# from django.contrib.auth.decorators import login_required
# from django.db.models import Q
# from .models import StudentLeave, CounselorLeave
# from authentication.models import Student, Counselor
#
#
# # Student views
# @login_required
# def student_leave(request):
#     """View for student leave application page"""
#     student = get_object_or_404(Student, user=request.user)
#
#     if request.method == 'POST':
#         date = request.POST.get('date')
#         reason = request.POST.get('reason')
#         no_of_days = request.POST.get('days')
#
#         # Create new leave application with Pending status
#         leave = StudentLeave.objects.create(
#             student=student,
#             date=date,
#             reason=reason,
#             no_of_days=no_of_days,
#             status='Pending'
#         )
#
#         return redirect('student_leave')
#
#     # Get all leave applications for this student
#     leave_records = StudentLeave.objects.filter(student=student).order_by('-date')
#
#     context = {
#         'student': student,
#         'leave_records': leave_records
#     }
#
#     return render(request, 'student_leave.html', context)
#
#
# # Counselor views
# @login_required
# def counselor_leave(request):
#     """View for counselor leave application page"""
#     counselor = get_object_or_404(Counselor, user=request.user)
#
#     # Get today's leave applications
#     today = timezone.now().date()
#     today_leaves = StudentLeave.objects.filter(
#         student__in=Student.objects.filter(counselor=counselor),
#         date=today
#     ).order_by('-date')
#
#     # Get all leave applications for records
#     all_leaves = StudentLeave.objects.filter(
#         student__in=Student.objects.filter(counselor=counselor)
#     ).order_by('-date')
#
#     context = {
#         'counselor': counselor,
#         'today_leaves': today_leaves,
#         'all_leaves': all_leaves
#     }
#
#     return render(request, 'counselor_leave.html', context)
#
#
# @login_required
# def update_leave_status(request):
#     """Handle leave status updates (approve/reject/reset)"""
#     if request.method == 'POST':
#         leave_id = request.POST.get('leave_id')
#         new_status = request.POST.get('status')
#
#         leave = get_object_or_404(StudentLeave, id=leave_id)
#         counselor = get_object_or_404(Counselor, user=request.user)
#
#         # Verify counselor is authorized for this student
#         if leave.student.counselor != counselor:
#             return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
#
#         # Check for 15-minute time window
#         try:
#             counselor_leave = CounselorLeave.objects.get(
#                 counselor=counselor,
#                 student=leave.student
#             )
#
#             # If status was previously changed and it's been over 15 minutes
#             if counselor_leave.status != 'Pending':
#                 time_diff = timezone.now() - timedelta(minutes=15)
#                 if counselor_leave.updated_at < time_diff:
#                     return JsonResponse({
#                         'success': False,
#                         'message': 'Cannot modify status after 15 minutes'
#                     }, status=400)
#
#         except CounselorLeave.DoesNotExist:
#             # Create new record if none exists
#             counselor_leave = CounselorLeave(
#                 counselor=counselor,
#                 student=leave.student
#             )
#
#         # Update leave status
#         leave.status = new_status
#         leave.save()
#
#         # Update counselor leave record
#         counselor_leave.status = new_status
#         counselor_leave.save()
#
#         return JsonResponse({'success': True})
#
#     return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
#
#
# @login_required
# def filter_leaves(request):
#     """Filter leave records by search term, month, or year"""
#     if request.method == 'GET':
#         search_term = request.GET.get('search', '')
#         month = request.GET.get('month', '')
#         year = request.GET.get('year', '')
#
#         counselor = get_object_or_404(Counselor, user=request.user)
#
#         # Start with all leaves for this counselor
#         leaves = StudentLeave.objects.filter(
#             student__in=Student.objects.filter(counselor=counselor)
#         )
#
#         # Apply filters
#         if search_term:
#             leaves = leaves.filter(
#                 Q(student__user__username__icontains=search_term) |
#                 Q(student__roll_number__icontains=search_term)
#             )
#
#         if month and month != 'Select':
#             leaves = leaves.filter(date__month=month)
#         if year and year != 'Select':
#             leaves = leaves.filter(date__year=year)
#
#         # Get today's leaves separately for the top section
#         today = timezone.now().date()
#         today_leaves = StudentLeave.objects.filter(
#             student__in=Student.objects.filter(counselor=counselor),
#             date=today
#         ).order_by('-date')
#
#         context = {
#             'counselor': counselor,
#             'today_leaves': today_leaves,
#             'all_leaves': leaves.order_by('-date')
#         }
#
#         return render(request, 'counselor_leave.html', context)
#
#     return redirect('counselor_leave')