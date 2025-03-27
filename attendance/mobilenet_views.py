import json
import base64
import numpy as np
import cv2
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from authentication.models import Student
from .mobilenet_frs import register_user_face, recognize_user, TRAIN_DIR
import os


@login_required
def mobilenet_profile(request):
    """Display student profile with mobilenet face recognition option"""
    try:
        student = Student.objects.get(user=request.user)
        return render(request, 'mobilenet_student_profile.html', {
            'student': student,
            'is_face_registered': check_face_registered(student)
        })
    except Student.DoesNotExist:
        return redirect('login')


def check_face_registered(student):
    """Check if the student has registered their face in the mobilenet system"""
    user_train_path = os.path.join(TRAIN_DIR, student.roll_number)
    return os.path.exists(user_train_path) and len(os.listdir(user_train_path)) > 0


@login_required
def mobilenet_check_registration(request):
    """Check if the current student has registered their face with mobilenet"""
    try:
        print(f"Checking MobileNet registration for user: {request.user.username}")
        student = Student.objects.get(user=request.user)
        is_registered = check_face_registered(student)
        print(f"MobileNet registration status for {student.roll_number}: {is_registered}")
        return JsonResponse({'is_registered': is_registered})
    except Student.DoesNotExist:
        print(f"Student not found for user: {request.user.username}")
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        print(f"Error checking MobileNet registration: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def mobilenet_register_face(request):
    """Process face registration using mobilenet system"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image')

            print(f"Received image data for MobileNet registration, length: {len(image_data) if image_data else 0}")

            if not image_data:
                return JsonResponse({
                    'success': False,
                    'message': 'No image data received'
                })

            # Handle both with and without the data:image prefix
            if ',' in image_data:
                # Format: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...
                image_data = image_data.split(',')[1]

            # Decode image
            try:
                image_bytes = base64.b64decode(image_data)
                image_array = np.frombuffer(image_bytes, np.uint8)
                frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                if frame is None:
                    return JsonResponse({
                        'success': False,
                        'message': 'Failed to decode image. Please try again with a different image.'
                    })

                # Get student from current user
                student = Student.objects.get(user=request.user)

                # Register face using the MobileNet system
                success, message = register_user_face(student, frame)

                return JsonResponse({
                    'success': success,
                    'message': message,
                    'username': student.user.username
                })

            except base64.binascii.Error as be:
                print(f"Base64 decoding error: {str(be)}")
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid image format: {str(be)}'
                })
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'success': False,
                    'message': f'Error processing image: {str(e)}'
                })

        except Student.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
        except json.JSONDecodeError as json_error:
            return JsonResponse({
                'success': False,
                'message': f'Invalid JSON data: {str(json_error)}'
            })
        except Exception as e:
            print(f"Error during MobileNet registration: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error during registration: {str(e)}'
            })

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@csrf_exempt
def mobilenet_recognize(request):
    """Test face recognition with mobilenet system"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image')

            if not image_data:
                return JsonResponse({
                    'success': False,
                    'message': 'No image data received'
                })

            # Handle both with and without the data:image prefix
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            # Decode image
            image_bytes = base64.b64decode(image_data)
            image_array = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if frame is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to decode image.'
                })

            # Recognize user
            username, confidence = recognize_user(frame)

            if username:
                return JsonResponse({
                    'success': True,
                    'recognized': True,
                    'username': username,
                    'confidence': float(confidence)
                })
            else:
                return JsonResponse({
                    'success': True,
                    'recognized': False,
                    'message': confidence  # This contains the error message if recognition failed
                })

        except Exception as e:
            print(f"Error during MobileNet recognition: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error during recognition: {str(e)}'
            })

    return JsonResponse({'error': 'Invalid request method'}, status=405)