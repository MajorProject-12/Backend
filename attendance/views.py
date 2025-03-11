# # views.py
# import cv2
# import numpy as np
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .models import FaceRegistration
# from .main import LightweightFRS
# import base64
# import json
#
#
# @csrf_exempt
# def register_face(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Method not allowed'}, status=405)
#
#     try:
#         data = json.loads(request.body)
#         image_data = data.get('image').split(',')[1]  # Remove data:image/jpeg;base64,
#         image_bytes = base64.b64decode(image_data)
#
#         # Convert to numpy array
#         nparr = np.frombuffer(image_bytes, np.uint8)
#         frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#
#         # Initialize FRS
#         frs = LightweightFRS()
#
#         # Check for face
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = frs.face_detector.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
#
#         if not faces:
#             return JsonResponse({'error': 'No face detected'}, status=400)
#
#         x, y, w, h = faces[0]
#         face_img = frame[y:y + h, x:x + w]
#
#         # Extract features
#         features = frs.extract_face_features(face_img)
#
#         # Check for spoofing
#         if not frs.check_spoof(frame):
#             return JsonResponse({'error': 'Spoof detected'}, status=400)
#
#         # Save to database
#         face_reg, created = FaceRegistration.objects.get_or_create(
#             user=request.user
#         )
#         face_reg.save_features(features)
#
#         # Convert face image to jpg for storage
#         _, img_encoded = cv2.imencode('.jpg', face_img)
#         face_reg.face_image.save(
#             f'face_{request.user.id}.jpg',
#             img_encoded.tobytes()
#         )
#         face_reg.is_active = True
#         face_reg.save()
#
#         return JsonResponse({'success': True})
#
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)