# attendance/views.py
import base64
import json
import numpy as np
import cv2
import time
import threading
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
from authentication.models import Student
from .models import Attendance, FaceRegistration
# from .frs import detect_face, extract_features, recognize_face, process_frame_with_dimensions
from .FasterRCNN_frs import detect_face, extract_features, recognize_face, process_frame_with_dimensions

# Maintain a global dictionary to store streams for each user session
active_streams = {}

class VideoCamera:
    def __init__(self, user_id):
        self.user_id = user_id
        self.frames = []
        self.is_active = True
        self.lock = threading.Lock()

    def add_frame(self, frame):
        with self.lock:
            self.frames.append(frame)
            # Keep only the last 30 frames (about 1-2 seconds at 15-30 fps)
            if len(self.frames) > 30:
                self.frames.pop(0)

    def get_frames(self):
        with self.lock:
            return self.frames.copy()

    def clear_frames(self):
        with self.lock:
            self.frames.clear()

    def stop(self):
        self.is_active = False

@login_required
def check_registration(request):
    """Check if the current student has registered their face"""
    try:
        print(f"Checking registration for user: {request.user.username}")
        student = Student.objects.get(user=request.user)
        is_registered = FaceRegistration.objects.filter(student=student).exists()
        print(f"Registration status for {student.roll_number}: {is_registered}")
        return JsonResponse({'is_registered': is_registered})
    except Student.DoesNotExist:
        print(f"Student not found for user: {request.user.username}")
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        print(f"Error checking registration: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def register_face(request):
    """Process face registration from webcam capture"""
    # Keeping this function as-is since it's working well
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image')

            # Add debugging to see what we're receiving
            print(f"Received image data length: {len(image_data) if image_data else 0}")

            # More robust base64 processing
            if image_data:
                # Handle both with and without the data:image prefix
                if ',' in image_data:
                    # Format: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...
                    image_data = image_data.split(',')[1]

                # Try decoding with error handling
                try:
                    image_bytes = base64.b64decode(image_data)
                    print(f"Decoded image bytes length: {len(image_bytes)}")

                    # Check if we have actual image data
                    if len(image_bytes) == 0:
                        print("Empty image data received")
                        return JsonResponse({
                            'success': False,
                            'message': 'Empty image data received. Please try again.',
                            'username': request.user.username
                        })

                    image_array = np.frombuffer(image_bytes, np.uint8)
                    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                    # Check if decoding was successful
                    if frame is None:
                        print("Failed to decode image")
                        return JsonResponse({
                            'success': False,
                            'message': 'Failed to decode image. Please try again with a different image.',
                            'username': request.user.username
                        })

                    print(f"Frame shape: {frame.shape}")

                    # Get student from current user
                    student = Student.objects.get(user=request.user)
                    print(f"Got student: {student.roll_number}")

                    # Detect face in the image using FRS - properly unpack the tuple
                    try:
                        print("Starting face detection...")
                        result = detect_face(frame)
                        print(f"Face detection result: {result[0] is not None if result else None}")
                    except Exception as face_detect_error:
                        print(f"Error in face detection: {str(face_detect_error)}")
                        import traceback
                        traceback.print_exc()
                        return JsonResponse({
                            'success': False,
                            'message': f'Face detection error: {str(face_detect_error)}',
                            'username': student.user.username
                        })

                    # Check if any face was detected
                    if result is None or result[0] is None:
                        print("No face detected in the image")
                        return JsonResponse({
                            'success': False,
                            'message': 'No face detected. Please ensure your face is clearly visible.',
                            'username': student.user.username
                        })

                    # Get the face area (first item in the tuple)
                    face_area = result[0]
                    print(f"Face area shape: {face_area.shape}")

                    # Extract facial features using FaceNet
                    try:
                        print("Extracting facial features...")
                        features = extract_features(face_area)
                        print(f"Features extracted, shape: {features.shape}")
                    except Exception as feature_extract_error:
                        print(f"Error extracting features: {str(feature_extract_error)}")
                        import traceback
                        traceback.print_exc()
                        return JsonResponse({
                            'success': False,
                            'message': f'Feature extraction error: {str(feature_extract_error)}',
                            'username': student.user.username
                        })

                    try:
                        # Save the face image and features in the database for the student
                        print(f"Saving face registration for student: {student.roll_number}")
                        face_registration, created = FaceRegistration.objects.get_or_create(student=student)
                        face_registration.face_features = features.tobytes()  # Store features in binary format

                        # Store the image in the database
                        _, buffer = cv2.imencode('.jpg', face_area)
                        from django.core.files.base import ContentFile
                        image_data = ContentFile(buffer.tobytes(), name=f'{student.roll_number}_face.jpg')
                        face_registration.face_image.save(f'{student.roll_number}_face.jpg', image_data)

                        face_registration.save()
                        print("Face registration saved successfully")
                    except Exception as db_error:
                        print(f"Database error: {str(db_error)}")
                        import traceback
                        traceback.print_exc()
                        return JsonResponse({
                            'success': False,
                            'message': f'Error saving to database: {str(db_error)}',
                            'username': student.user.username
                        })

                    return JsonResponse({
                        'success': True,
                        'message': 'Face registered successfully',
                        'username': student.user.username
                    })

                except base64.binascii.Error as be:
                    print(f"Base64 decoding error: {str(be)}")
                    return JsonResponse({
                        'success': False,
                        'message': f'Invalid image format: {str(be)}',
                        'username': request.user.username
                    })
                except Exception as e:
                    print(f"Unexpected error processing image: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return JsonResponse({
                        'success': False,
                        'message': f'Error processing image: {str(e)}',
                        'username': request.user.username
                    })
            else:
                print("No image data received")
                return JsonResponse({
                    'success': False,
                    'message': 'No image data received',
                    'username': request.user.username
                })

        except Student.DoesNotExist:
            print("Student not found error")
            return JsonResponse({'error': 'Student not found'}, status=404)
        except json.JSONDecodeError as json_error:
            print(f"JSON decode error: {str(json_error)}")
            return JsonResponse({
                'success': False,
                'message': f'Invalid JSON data: {str(json_error)}',
                'username': request.user.username if request.user else None
            })
        except Exception as e:
            print(f"Error during registration: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error during registration: {str(e)}',
                'username': request.user.username if request.user else None
            })

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def student_check_in(request):
    """Display the student check-in page with current attendance status"""
    try:
        student = Student.objects.get(user=request.user)
        today = datetime.now().date()

        # Get today's attendance status if it exists
        try:
            today_attendance = Attendance.objects.get(student=student, date=today)
            today_status = today_attendance.status
        except Attendance.DoesNotExist:
            today_status = "Not Marked"

        # Format today's date
        today_date = today.strftime("%A, %B %d, %Y")

        return render(request, 'student_check_in.html', {
            'student': student,
            'today_date': today_date,
            'today_status': today_status
        })
    except Student.DoesNotExist:
        return redirect('login')  # Redirect to login if student not found
    except Exception as e:
        print(f"Error in student_check_in view: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, "An error occurred while loading the check-in page.")
        return redirect('student_dashboard')  # Fallback to dashboard

@login_required
@csrf_exempt
def receive_video_frame(request):
    """Receive video frames from client for attendance processing"""
    if request.method == 'POST':
        try:
            # Get or create the video stream for this user
            user_id = request.user.id
            if user_id not in active_streams:
                active_streams[user_id] = VideoCamera(user_id)

            # Process the frame data
            data = json.loads(request.body)
            frame_data = data.get('frame')

            if frame_data:
                # Handle data URI format
                if ',' in frame_data:
                    frame_data = frame_data.split(',')[1]

                # Decode the frame
                try:
                    image_bytes = base64.b64decode(frame_data)
                    image_array = np.frombuffer(image_bytes, np.uint8)
                    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                    if frame is not None:
                        # Store the frame in the user's stream
                        active_streams[user_id].add_frame(frame)
                        return JsonResponse({'success': True})
                    else:
                        return JsonResponse({'success': False, 'message': 'Invalid frame data'})
                except Exception as e:
                    print(f"Error processing frame: {str(e)}")
                    return JsonResponse({'success': False, 'message': str(e)})
            else:
                return JsonResponse({'success': False, 'message': 'No frame data received'})
        except Exception as e:
            print(f"Error in receive_video_frame: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def start_attendance_verification(request):
    """Start the attendance verification process using the accumulated frames"""
    if request.method == 'POST':
        try:
            user_id = request.user.id
            if user_id not in active_streams or len(active_streams[user_id].get_frames()) == 0:
                return JsonResponse({
                    'success': False,
                    'message': 'No video frames available. Please ensure your camera is working.'
                })

            # Get the student
            student = Student.objects.get(user=request.user)

            # Check if student has registered their face
            try:
                face_registration = FaceRegistration.objects.get(student=student)
            except FaceRegistration.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Face not registered yet. Please register your face in your profile first.'
                })

            # Get registered face features
            registered_features = np.frombuffer(face_registration.face_features, dtype=np.float32)

            # Get frames for processing
            frames = active_streams[user_id].get_frames()
            print(f"Processing {len(frames)} frames for attendance verification")

            # Use recognize_face_web function with collected frames
            try:
                # Import the necessary modules
                from .frs import recognize_face_web
                import importlib

                # Set up global frames for processing
                frs_module = importlib.import_module('.frs', package=__package__)
                frs_module.web_frames = frames
                frs_module.current_frame_index = 0

                # Run the face recognition
                recognition_result = recognize_face_web(registered_features)
                print(f"Recognition result: {recognition_result}")

                if recognition_result:
                    # Mark attendance
                    try:
                        attendance, created = Attendance.objects.get_or_create(
                            student=student,
                            date=datetime.now().date(),
                            defaults={'status': 'Present'}
                        )

                        if not created:
                            attendance.status = 'Present'
                            attendance.save()
                            print("Updated existing attendance record to Present")
                        else:
                            print("Created new attendance record")

                        # Clear frames after successful attendance
                        active_streams[user_id].clear_frames()

                        return JsonResponse({
                            'success': True,
                            'message': 'Attendance marked successfully!'
                        })
                    except Exception as db_error:
                        print(f"Database error: {str(db_error)}")
                        import traceback
                        traceback.print_exc()
                        return JsonResponse({
                            'success': False,
                            'message': f'Error saving attendance: {str(db_error)}'
                        })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Verification failed. Please ensure proper lighting, face visibility, and follow the prompts to blink naturally.'
                    })
            except Exception as recog_error:
                print(f"Error in face recognition: {str(recog_error)}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'success': False,
                    'message': f'Face recognition error: {str(recog_error)}'
                })
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
        except Exception as e:
            print(f"Error during attendance verification: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error during attendance verification: {str(e)}'
            })

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def stop_video_stream(request):
    """Stop the video stream and clean up resources"""
    if request.method == 'POST':
        user_id = request.user.id
        if user_id in active_streams:
            active_streams[user_id].stop()
            del active_streams[user_id]
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid request method'}, status=405)

# This function keeps the original implementation for compatibility
@login_required
@csrf_exempt
def mark_attendance(request):
    """Mark attendance using face recognition with liveness detection"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image')
            frames_data = data.get('frames', [])

            # Handle single image for backward compatibility
            if image_data and not frames_data:
                frames_data = [image_data]

            if not frames_data:
                return JsonResponse({
                    'success': False,
                    'message': 'No image data received'
                })

            print(f"Received {len(frames_data)} frames for attendance check-in")

            # Decode all frames
            frames = []
            for frame_data in frames_data:
                try:
                    # Handle data URI format
                    if ',' in frame_data:
                        frame_data = frame_data.split(',')[1]

                    image_bytes = base64.b64decode(frame_data)
                    image_array = np.frombuffer(image_bytes, np.uint8)
                    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                    if frame is not None:
                        frames.append(frame)
                except Exception as e:
                    print(f"Error decoding frame: {str(e)}")
                    continue

            if not frames:
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to decode any valid images. Please try again.'
                })

            print(f"Successfully decoded {len(frames)} frames")

            # Get the student
            student = Student.objects.get(user=request.user)
            print(f"Checking attendance for student: {student.roll_number}")

            # Check if student has registered their face
            try:
                face_registration = FaceRegistration.objects.get(student=student)
                print(f"Found face registration for student: {student.roll_number}")
            except FaceRegistration.DoesNotExist:
                print(f"No face registration found for student: {student.roll_number}")
                return JsonResponse({
                    'success': False,
                    'message': 'Face not registered yet. Please register your face in your profile first.'
                })

            # Get registered face features
            registered_features = np.frombuffer(face_registration.face_features, dtype=np.float32)

            # Use recognize_face_web function with the video stream approach
            try:
                print("Starting face recognition with liveness detection...")

                # Import the necessary modules and functions
                from .frs import recognize_face_web
                import cv2

                # Set up global frames for the video stream
                import sys
                # Add global variables to frs module
                import importlib
                frs_module = importlib.import_module('.frs', package=__package__)
                frs_module.web_frames = frames
                frs_module.current_frame_index = 0

                # Call the function that uses video stream-like processing
                recognition_result = recognize_face_web(registered_features)
                print(f"Recognition result: {recognition_result}")

                if recognition_result:
                    # Mark attendance
                    try:
                        print(f"Marking attendance for student: {student.roll_number}")
                        attendance, created = Attendance.objects.get_or_create(
                            student=student,
                            date=datetime.now().date(),
                            defaults={'status': 'Present'}
                        )

                        if not created:
                            attendance.status = 'Present'
                            attendance.save()
                            print("Updated existing attendance record to Present")
                        else:
                            print("Created new attendance record")

                        return JsonResponse({
                            'success': True,
                            'message': 'Attendance marked successfully!',
                        })
                    except Exception as db_error:
                        print(f"Database error: {str(db_error)}")
                        import traceback
                        traceback.print_exc()
                        return JsonResponse({
                            'success': False,
                            'message': f'Error saving attendance: {str(db_error)}'
                        })
                else:
                    print("Face recognition or liveness verification failed")
                    return JsonResponse({
                        'success': False,
                        'message': 'Verification failed. Please ensure proper lighting, face visibility, and follow the prompts to blink naturally.'
                    })
            except Exception as recog_error:
                print(f"Error in face recognition: {str(recog_error)}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'success': False,
                    'message': f'Face recognition error: {str(recog_error)}'
                })

        except Student.DoesNotExist:
            print("Student not found error")
            return JsonResponse({'error': 'Student not found'}, status=404)
        except json.JSONDecodeError as json_error:
            print(f"JSON decode error: {str(json_error)}")
            return JsonResponse({
                'success': False,
                'message': f'Invalid JSON data: {str(json_error)}'
            })
        except Exception as e:
            print(f"Error during attendance marking: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error during attendance marking: {str(e)}'
            })

    return JsonResponse({'error': 'Invalid request method'}, status=405)