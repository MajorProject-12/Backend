from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Remark
from authentication.models import Student, Counselor

@login_required
def counselor_remarks(request):
    """ View for counselors to manage student remarks. """
    counselor = get_object_or_404(Counselor, user=request.user)
    students = Student.objects.filter(assigned_counselor=counselor)
    remarks = Remark.objects.filter(student__in=students).order_by('-date_created')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        content = request.POST.get('content')

        if student_id and content:
            student = get_object_or_404(Student, id=student_id)
            Remark.objects.create(student=student, counselor=counselor, content=content)
            return JsonResponse({'message': 'Remark added successfully!'}, status=201)

    return render(request, 'counselor_remarks.html', {'students': students, 'remarks': remarks})


@login_required
def student_remarks(request):
    """ View for students to see their own remarks. """
    student = get_object_or_404(Student, user=request.user)
    remarks = Remark.objects.filter(student=student).order_by('-date_created')

    return render(request, 'student_remarks.html', {'remarks': remarks})


@login_required
def delete_remark(request, remark_id):
    """ View for counselors to delete a remark. """
    remark = get_object_or_404(Remark, id=remark_id)

    if request.user == remark.counselor.user:
        remark.delete()
        return JsonResponse({'message': 'Remark deleted successfully!'}, status=200)

    return JsonResponse({'error': 'Unauthorized'}, status=403)
