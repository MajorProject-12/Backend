import cv2
import numpy as np
import time
import mediapipe as mp
from keras_facenet import FaceNet
from sklearn.preprocessing import normalize
from scipy.spatial.distance import cosine
from scipy.spatial import distance as dist
import math
from skimage import feature

# Initialize the FaceNet embedder
embedder = FaceNet()

# Initialize MediaPipe Face Mesh with fixed parameters to prevent warnings
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    static_image_mode=False
)

# MediaPipe indices for the left and right eyes
LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]

# Key facial landmarks for depth analysis
DEPTH_LANDMARKS = [1, 4, 152, 234, 454]

# Updated fusion weights to prioritize blink detection (part of static)
FUSION_WEIGHTS = {
    'static': 0.6,  # EAR/depth (increased from 0.3 to prioritize blink)
    'dynamic': 0.4  # Micro-movements (decreased from 0.7)
}

# Adjust validation weights to downplay texture and emphasize blink even more
VALIDATION_WEIGHTS = {
    'blink': 0.5,  # Increased from 0.4
    'depth': 0.3,  # Kept same
    'dynamic': 0.15,  # Reduced from 0.2
    'texture': 0.05  # Reduced from 0.1 since it's often failing
}

# New function to process frame with dimensions
def process_frame_with_dimensions(frame):
    h, w, _ = frame.shape

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Set image dimensions before processing
    rgb_frame.flags.writeable = False

    # Process with dimensions
    results = face_mesh.process(rgb_frame)

    # Reset writeable flag
    rgb_frame.flags.writeable = True

    return results, h, w

# Preprocess the image for FaceNet
def preprocess_image(image):
    img = cv2.resize(image, (160, 160))
    return np.expand_dims(img, axis=0)


# Extract features from an image using FaceNet
def extract_features(img):
    img = preprocess_image(img)
    features = embedder.embeddings(img)
    normalized_features = normalize(features)
    return normalized_features.flatten()


# Calculate Eye Aspect Ratio (EAR)
def calculate_ear(eye_landmarks):
    # Calculate the vertical distances
    A = dist.euclidean(eye_landmarks[1], eye_landmarks[4])
    B = dist.euclidean(eye_landmarks[2], eye_landmarks[5])

    # Calculate the horizontal distance
    C = dist.euclidean(eye_landmarks[0], eye_landmarks[3])

    # Calculate the eye aspect ratio
    ear = (A + B) / (2.0 * C)
    return ear


# Detect face and extract face area using MediaPipe with 3D data
def detect_face(frame):
    h, w, _ = frame.shape

    # Convert the BGR image to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame to find facial landmarks
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        face_landmarks = results.multi_face_landmarks[0]

        # Get facial bounding box
        x_min, y_min = w, h
        x_max, y_max = 0, 0

        for landmark in face_landmarks.landmark:
            x, y = int(landmark.x * w), int(landmark.y * h)
            x_min = min(x_min, x)
            y_min = min(y_min, y)
            x_max = max(x_max, x)
            y_max = max(y_max, y)

        # Add padding to the face area
        padding = 20
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = min(w, x_max + padding)
        y_max = min(h, y_max + padding)

        # Make sure we have valid face area before extraction
        if x_min < x_max and y_min < y_max:
            face_area = frame[y_min:y_max, x_min:x_max]
        else:
            return None, None, None, None, None

        # Get landmarks for EAR calculation and 3D analysis
        landmarks_2d = []  # 2D landmarks for eye aspect ratio
        landmarks_3d = []  # 3D landmarks for depth analysis

        for landmark in face_landmarks.landmark:
            landmarks_2d.append([landmark.x * w, landmark.y * h])
            landmarks_3d.append([landmark.x * w, landmark.y * h, landmark.z * w])

        landmarks_2d = np.array(landmarks_2d)
        landmarks_3d = np.array(landmarks_3d)

        # Extract eye landmarks for EAR
        left_eye = [landmarks_2d[i] for i in LEFT_EYE_INDICES]
        right_eye = [landmarks_2d[i] for i in RIGHT_EYE_INDICES]

        # Get depth landmarks for 3D analysis
        depth_points = [landmarks_3d[i] for i in DEPTH_LANDMARKS]

        face_box = (x_min, y_min, x_max - x_min, y_max - y_min)

        return face_area, (left_eye, right_eye), face_box, depth_points, landmarks_3d


# Calculate depth variance to detect flat surfaces (like photos)
def analyze_depth(depth_points):
    # Extract z-coordinates
    z_values = [point[2] for point in depth_points]

    # Calculate variance of depth
    depth_variance = np.var(z_values)

    # Calculate range of depth in mm (approximate conversion)
    depth_range = (max(z_values) - min(z_values)) * 1000

    return depth_variance, depth_range


# Detect head movement with 3D rotation analysis
def detect_head_movement(current_landmarks, previous_landmarks, threshold=0.35):
    if previous_landmarks is None or len(previous_landmarks) == 0:
        return False, 0, (0, 0)

    # Calculate movement of key landmarks
    movement = 0
    pitch_angles = []
    yaw_angles = []

    for i in DEPTH_LANDMARKS:
        if i < len(current_landmarks) and i < len(previous_landmarks):
            # Calculate movement vector
            dx = current_landmarks[i][0] - previous_landmarks[i][0]
            dy = current_landmarks[i][1] - previous_landmarks[i][1]
            dz = current_landmarks[i][2] - previous_landmarks[i][2]

            # Calculate magnitude of movement (optical flow)
            dist_val = math.sqrt(dx * dx + dy * dy + dz * dz)
            movement += dist_val

            # Calculate approximate pitch (vertical) and yaw (horizontal) angles
            # This is a simplified approximation
            if abs(dz) > 0.001:  # Avoid division by zero
                pitch = math.degrees(math.atan2(dy, dz))
                yaw = math.degrees(math.atan2(dx, dz))
                pitch_angles.append(pitch)
                yaw_angles.append(yaw)

    # Average movement across landmarks
    avg_movement = movement / len(DEPTH_LANDMARKS)

    # Average pitch and yaw
    avg_pitch = np.mean(pitch_angles) if pitch_angles else 0
    avg_yaw = np.mean(yaw_angles) if yaw_angles else 0

    # Return if movement exceeds threshold and rotation angles
    return avg_movement > threshold, avg_movement, (avg_pitch, avg_yaw)

# Detect micro-movements with temporal consistency
def detect_micro_movements(landmarks_history, frames=8):
    if len(landmarks_history) < frames:
        return False, 0

    # Calculate the variance of each landmark position over time
    all_variances = []

    for i in range(min(5, len(landmarks_history[0]))):  # Look at a few key landmarks
        x_values = [frame[i][0] for frame in landmarks_history[-frames:]]
        y_values = [frame[i][1] for frame in landmarks_history[-frames:]]
        z_values = [frame[i][2] for frame in landmarks_history[-frames:]]

        var_x = np.var(x_values)
        var_y = np.var(y_values)
        var_z = np.var(z_values)

        all_variances.extend([var_x, var_y, var_z])

    avg_variance = np.mean(all_variances)

    # Real faces have small natural micro-movements
    # Updated thresholds based on research
    is_natural = 0.01 < avg_variance < 12.0

    return is_natural, avg_variance

# Texture analysis with LBP for replay detection
def analyze_texture_lbp(face_img):
    if face_img is None or face_img.size == 0:
        return False, 0

    # Convert to grayscale
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)

    # Compute LBP features
    radius = 1
    n_points = 8 * radius
    lbp = feature.local_binary_pattern(gray, n_points, radius, method="uniform")

    # Compute histogram
    n_bins = int(lbp.max() + 1)
    hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins), density=True)

    # Calculate entropy of LBP histogram (measure of texture complexity)
    entropy = -np.sum(hist * np.log2(hist + 1e-10))

    # Calculate uniformity of texture (less uniform for real faces)
    uniformity = np.sum(hist * hist)

    # Real faces typically have high entropy and low uniformity
    # ICCV 2023 threshold = 0.45
    is_real_face = entropy > 4.5 and uniformity < 0.45

    return is_real_face, (entropy, uniformity)

# Adaptive lighting-based EAR threshold
def get_adaptive_ear_threshold(frame):
    # Calculate average brightness of the frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)

    # Adjust threshold based on lighting conditions
    # Darker environments need lower threshold (harder to detect blinks)
    if brightness < 80:  # Low light
        return 0.18
    elif brightness > 200:  # Very bright light
        return 0.25
    else:  # Normal lighting
        return 0.22

# Register a student's face
def register_student():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam. Check your camera connection.")
            return None

        print("Press 'q' to capture student's face for registration.")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame. Check your camera.")
                break
            cv2.imshow("Live Capture", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        face, _, _, _, _ = detect_face(frame)
        if face is not None:
            features = extract_features(face)
            print("Registration complete!")
            return features
        else:
            print("No face detected. Please try again in better lighting.")
            return None
    except Exception as e:
        print(f"Error during registration: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# Recognize a face using the webcam with 2023-2024 anti-spoofing measures
def recognize_face(registered_features):
    # Initialize variables
    ear_values = []
    blink_frames = 0
    total_blinks = 0
    movement_frames = 0
    blink_detected = False
    movement_detected = False
    rotation_detected = False
    depth_verified = False
    texture_verified = False
    micro_movements_verified = False
    in_blink = False

    # Initialize variables for error reporting
    depth_variance = 0.0
    depth_range = 0.0
    verification_score = 0.0
    face = None

    # Detection parameters with increased sensitivity
    BLINK_CONSEC_FRAMES = 1  # Just 1 frame needed to count as blink starting
    BLINK_TOTAL_REQUIRED = 2  # Reduced from 3 to 2 required blinks
    DEPTH_VARIANCE_THRESHOLD = 800.0  # Updated: 800-1500 for RGB cameras
    DEPTH_RANGE_THRESHOLD = 30.0  # Updated: 30-80mm
    MOVEMENT_THRESHOLD = 0.35  # Updated: 0.35-0.6 magnitude threshold
    MOVEMENT_FRAMES_REQUIRED = 8  # Updated: 7-10 frame window
    ROTATION_THRESHOLD = 4.0  # Updated: 4°-8° for pitch/yaw

    # History of data for temporal analysis
    prev_landmarks = None
    landmarks_history = []
    frame_history = []
    pitch_yaw_history = []

    # For displaying status
    font = cv2.FONT_HERSHEY_SIMPLEX
    start_time = time.time()
    timeout = 30

    # Verification scores for weighted fusion
    scores = {'blink': 0, 'depth': 0, 'dynamic': 0, 'texture': 0}

    # Open camera
    cap = cv2.VideoCapture(0)
    print("Looking for face... Please blink naturally and move your head slightly for verification.")

    try:
        # Main processing loop
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame.")
                break

            # Store frame for temporal analysis
            frame_history.append(frame.copy())
            if len(frame_history) > 20:
                frame_history.pop(0)

            # Make a copy for display
            display_frame = frame.copy()

            # Get general lighting threshold
            EAR_THRESHOLD = get_adaptive_ear_threshold(frame)

            # Detect face and landmarks
            try:
                face, eye_landmarks, face_box, depth_points, landmarks_3d = detect_face(frame)
            except Exception as e:
                print(f"Error in face detection: {str(e)}")
                cv2.putText(display_frame, "Face detection error", (10, 30), font, 0.7, (0, 0, 255), 2)
                cv2.imshow("Liveness Detection", display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            if face is not None and eye_landmarks is not None and depth_points is not None:
                left_eye, right_eye = eye_landmarks

                # Calculate EAR for both eyes
                left_ear = calculate_ear(left_eye)
                right_ear = calculate_ear(right_eye)

                # Average EAR
                ear = (left_ear + right_ear) / 2.0
                ear_values.append(ear)

                # Smooth EAR to reduce noise
                if len(ear_values) > 3:
                    ear = np.mean(ear_values[-3:])

                # Store landmarks history for movement analysis
                landmarks_history.append(landmarks_3d)
                if len(landmarks_history) > 30:
                    landmarks_history.pop(0)

                # Analyze depth for flat surface detection
                try:
                    depth_variance, depth_range = analyze_depth(depth_points)
                    if depth_variance > DEPTH_VARIANCE_THRESHOLD and depth_range > DEPTH_RANGE_THRESHOLD:
                        depth_verified = True
                        scores['depth'] = min(1.0, depth_variance / DEPTH_VARIANCE_THRESHOLD * 0.8)
                except Exception as e:
                    print(f"Error analyzing depth: {str(e)}")
                    depth_variance = 0
                    depth_range = 0

                # Detect head movement with rotation analysis
                try:
                    is_moving, movement_amount, (pitch, yaw) = detect_head_movement(
                        landmarks_3d, prev_landmarks, MOVEMENT_THRESHOLD)

                    # Store pitch/yaw for rotation analysis
                    pitch_yaw_history.append((pitch, yaw))
                    if len(pitch_yaw_history) > 10:
                        pitch_yaw_history.pop(0)

                    # Check for significant rotation
                    if len(pitch_yaw_history) >= 5:
                        max_pitch = max([abs(p) for p, _ in pitch_yaw_history])
                        max_yaw = max([abs(y) for _, y in pitch_yaw_history])
                        if max_pitch > ROTATION_THRESHOLD or max_yaw > ROTATION_THRESHOLD:
                            rotation_detected = True

                    if is_moving:
                        movement_frames += 1
                    else:
                        movement_frames = max(0, movement_frames - 1)  # Decrease counter if not moving

                    if movement_frames >= MOVEMENT_FRAMES_REQUIRED:
                        movement_detected = True
                        scores['dynamic'] = min(1.0, movement_frames / MOVEMENT_FRAMES_REQUIRED * 0.9)
                except Exception as e:
                    print(f"Error detecting head movement: {str(e)}")
                    is_moving = False
                    movement_amount = 0
                    pitch = 0
                    yaw = 0

                # Update previous landmarks
                prev_landmarks = landmarks_3d

                # Detect micro-movements
                if len(landmarks_history) > 10:
                    try:
                        is_natural, micro_var = detect_micro_movements(landmarks_history, frames=8)
                        if is_natural:
                            micro_movements_verified = True
                            scores['dynamic'] = max(scores['dynamic'], min(1.0, micro_var / 5.0 * 0.7))
                    except Exception as e:
                        print(f"Error detecting micro-movements: {str(e)}")
                        is_natural = False
                        micro_var = 0

                # Texture analysis for replay detection
                if len(frame_history) > 10 and len(ear_values) % 5 == 0:
                    try:
                        is_real_face, (entropy, uniformity) = analyze_texture_lbp(face)
                        if is_real_face:
                            texture_verified = True
                            scores['texture'] = min(1.0, entropy / 6.0 * 0.8)
                    except Exception as e:
                        print(f"Error in texture analysis: {str(e)}")
                        is_real_face = False

                # Draw face box
                x, y, w, h = face_box
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Track blinks - adaptive methodology with enhanced sensitivity for high EAR values
                if len(ear_values) > 5:
                    # Calculate baseline EAR for this person (average of max values)
                    if len(ear_values) > 20:
                        baseline_ear = np.mean(sorted(ear_values[-20:])[-10:])
                    else:
                        baseline_ear = np.mean(sorted(ear_values)[-int(len(ear_values) / 2):])

                    # If we have very high EAR values (>0.4), adjust the sensitivity
                    ear_multiplier = 0.90 if baseline_ear > 0.4 else 0.85

                    # Calculate relative threshold based on person's baseline
                    personal_threshold = baseline_ear * ear_multiplier  # 10-15% reduction from baseline is a blink

                    recent_min_ear = min(ear_values[-5:])
                    recent_max_ear = max(ear_values[-5:])

                    # For high EAR values, use a smaller ratio
                    min_ear_change_ratio = 0.05 if baseline_ear > 0.4 else 0.1
                    ear_change_ratio = (recent_max_ear - recent_min_ear) / recent_max_ear

                    # More sensitive blink detection based on significant drop from baseline
                    if (ear_change_ratio > min_ear_change_ratio or
                        (recent_max_ear - ear) > 0.02) and not in_blink and ear < personal_threshold:
                        blink_frames += 1
                        if blink_frames >= BLINK_CONSEC_FRAMES:
                            in_blink = True
                            cv2.putText(display_frame, "BLINK STARTING", (10, 60), font, 0.7, (255, 0, 0), 2)
                    elif in_blink and ear > (personal_threshold * 1.02):  # Reduced from 1.05
                        in_blink = False
                        total_blinks += 1
                        blink_frames = 0
                        cv2.putText(display_frame, f"BLINK DETECTED! Total: {total_blinks}/{BLINK_TOTAL_REQUIRED}",
                                    (10, 60), font, 0.7, (255, 0, 0), 2)

                    # Display personal threshold for debugging
                    cv2.putText(display_frame,
                                f"Personal threshold: {personal_threshold:.2f} (Baseline: {baseline_ear:.2f})",
                                (10, 250), font, 0.6, (0, 0, 255), 2)

                # Check if we have enough blinks
                if total_blinks >= BLINK_TOTAL_REQUIRED:
                    blink_detected = True
                    scores['blink'] = 1.0  # Always give full score when required blinks detected
                elif total_blinks > 0:
                    # Partial credit for at least one blink
                    blink_detected = False
                    scores['blink'] = 0.7  # 70% credit for partial blinks

                # Display status information
                cv2.putText(display_frame, f"EAR: {ear:.2f} (Threshold: {EAR_THRESHOLD:.2f})", (10, 30), font, 0.6,
                            (0, 0, 255), 2)
                cv2.putText(display_frame, f"Depth variance: {depth_variance:.1f}", (10, 90), font, 0.6, (0, 0, 255), 2)
                cv2.putText(display_frame, f"Depth range: {depth_range:.1f}mm", (10, 120), font, 0.6, (0, 0, 255), 2)
                cv2.putText(display_frame, f"Movement: {movement_amount:.2f}", (10, 150), font, 0.6, (0, 0, 255), 2)

                if len(pitch_yaw_history) > 0:
                    cv2.putText(display_frame, f"Rotation: P:{pitch:.1f}° Y:{yaw:.1f}°", (10, 180), font, 0.6,
                                (0, 0, 255),
                                2)

                # Display verification status with blink as primary
                y_pos = 210
                # Prioritize blink detection in display
                if blink_detected:
                    cv2.putText(display_frame, "✓ Blink verified (PRIMARY)", (10, y_pos), font, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(display_frame,
                                f"× Blink detection ({total_blinks}/{BLINK_TOTAL_REQUIRED}) - PRIMARY CHECK",
                                (10, y_pos), font, 0.7, (255, 255, 0), 2)
                y_pos += 30

                if depth_verified:
                    cv2.putText(display_frame, "✓ Depth verified", (10, y_pos), font, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(display_frame, "× Depth verification", (10, y_pos), font, 0.7, (255, 255, 0), 2)
                y_pos += 30

                status_text = "× Movement verification"
                if movement_detected and rotation_detected:
                    status_text = "✓ Movement & rotation verified"
                    scores['dynamic'] = max(scores['dynamic'], 0.85)
                elif movement_detected:
                    status_text = "✓ Movement verified"
                elif rotation_detected:
                    status_text = "✓ Rotation verified"

                cv2.putText(display_frame, status_text, (10, y_pos), font, 0.7,
                            (0, 255, 0) if movement_detected or rotation_detected else (255, 255, 0), 2)

                if not (movement_detected or rotation_detected):
                    cv2.putText(display_frame, "Please turn your head slightly", (10, y_pos + 30), font, 0.7,
                                (255, 255, 0),
                                2)
                    y_pos += 30

                y_pos += 30

                if micro_movements_verified:
                    cv2.putText(display_frame, "✓ Micro-movements verified", (10, y_pos), font, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(display_frame, "× Analyzing micro-movements", (10, y_pos), font, 0.7, (255, 255, 0), 2)
                y_pos += 30

                if texture_verified:
                    cv2.putText(display_frame, "✓ Texture analysis passed", (10, y_pos), font, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(display_frame, "× Analyzing texture patterns", (10, y_pos), font, 0.7, (255, 255, 0), 2)

                # Calculate weighted verification score with blink prioritized
                verification_score = (
                        VALIDATION_WEIGHTS['blink'] * scores['blink'] +
                        VALIDATION_WEIGHTS['depth'] * scores['depth'] +
                        VALIDATION_WEIGHTS['dynamic'] * scores['dynamic'] +
                        VALIDATION_WEIGHTS['texture'] * scores['texture']
                )

                # Modified verification logic with higher priority for blink
                static_score = depth_verified
                dynamic_score = movement_detected or rotation_detected or micro_movements_verified

                # Final verification requires:
                # 1. Blink detection is required (or at least 1 blink)
                # 2. Either static verification (weighted 0.6) or dynamic verification (weighted 0.4)
                # 3. AND a combined score of at least 0.5
                final_verification = (
                        (blink_detected or total_blinks >= 1) and  # Even 1 blink is acceptable
                        (static_score * FUSION_WEIGHTS['static'] +
                         dynamic_score * FUSION_WEIGHTS['dynamic'] >= 0.4)  # Reduced from 0.5
                        and verification_score >= 0.5  # Reduced from 0.6
                )

                # Display verification score
                cv2.putText(display_frame, f"Verification score: {verification_score:.2f}",
                            (10, display_frame.shape[0] - 80), font, 0.7,
                            (0, 255, 0) if verification_score >= 0.5 else (0, 255, 255), 2)

                if final_verification:
                    cv2.putText(display_frame, "LIVENESS VERIFIED", (10, display_frame.shape[0] - 50),
                                font, 1.0, (0, 255, 0), 2)
                    # Show verification message for a moment
                    cv2.imshow("Liveness Detection", display_frame)
                    cv2.waitKey(1000)
                    break
            else:
                cv2.putText(display_frame, "No face detected", (10, 30), font, 0.7, (0, 0, 255), 2)
                scores = {'blink': 0, 'depth': 0, 'dynamic': 0, 'texture': 0}

            # Display the remaining time
            try:
                elapsed_time = time.time() - start_time
                remaining_time = max(0, timeout - int(elapsed_time))
                cv2.putText(display_frame, f"Time remaining: {remaining_time}s", (10, display_frame.shape[0] - 20),
                            font, 0.7, (0, 0, 255), 2)
            except Exception as e:
                print(f"Error displaying time: {str(e)}")

            # Create EAR visualization graph
            try:
                if len(ear_values) > 0:
                    # Plot the EAR values in a scrolling graph
                    graph_width = 500
                    graph_height = 200
                    graph_margin = 50

                    # Create the graph background
                    graph_img = np.ones((graph_height + 2 * graph_margin, graph_width + 2 * graph_margin, 3),
                                        dtype=np.uint8) * 255

                    # Draw the axes
                    cv2.line(graph_img, (graph_margin, graph_height + graph_margin),
                             (graph_width + graph_margin, graph_height + graph_margin), (0, 0, 0), 2)  # X-axis
                    cv2.line(graph_img, (graph_margin, graph_margin),
                             (graph_margin, graph_height + graph_margin), (0, 0, 0), 2)  # Y-axis

                    # Draw the EAR threshold line
                    threshold_y = graph_height + graph_margin - int(EAR_THRESHOLD * graph_height)
                    cv2.line(graph_img, (graph_margin, threshold_y),
                             (graph_width + graph_margin, threshold_y), (255, 0, 0), 2)  # Threshold line

                    # Draw the EAR values
                    history_length = min(graph_width, len(ear_values))
                    points = []
                    for i in range(history_length):
                        idx = len(ear_values) - history_length + i
                        x = graph_margin + int(i * graph_width / history_length)
                        y = graph_height + graph_margin - int(ear_values[idx] * graph_height)
                        points.append((x, y))

                    # Draw the EAR line
                    if len(points) > 1:
                        for i in range(len(points) - 1):
                            cv2.line(graph_img, points[i], points[i + 1], (0, 255, 0), 2)

                    # Add labels
                    cv2.putText(graph_img, "EAR", (10, 20), font, 0.7, (0, 0, 0), 2)
                    cv2.putText(graph_img, "Time", (graph_width, graph_height + 2 * graph_margin - 10), font, 0.7,
                                (0, 0, 0), 2)
                    cv2.putText(graph_img, f"Threshold: {EAR_THRESHOLD:.2f}", (graph_margin, threshold_y - 10), font,
                                0.5,
                                (255, 0, 0), 1)

                    # Show the graph
                    cv2.imshow("EAR Graph", graph_img)
            except Exception as e:
                print(f"Error creating EAR graph: {str(e)}")

            # Display frame
            cv2.imshow("Liveness Detection", display_frame)

            # Check for exit conditions
            key = cv2.waitKey(1) & 0xFF
            if (key == ord('q')) or (elapsed_time > timeout):
                break

        # Release resources outside the loop but still inside the try block
        cap.release()
        cv2.destroyAllWindows()

        # Calculate final verification results
        try:
            # Calculate weighted verification score with blink prioritized
            verification_score = (
                    VALIDATION_WEIGHTS['blink'] * scores['blink'] +
                    VALIDATION_WEIGHTS['depth'] * scores['depth'] +
                    VALIDATION_WEIGHTS['dynamic'] * scores['dynamic'] +
                    VALIDATION_WEIGHTS['texture'] * scores['texture']
            )

            # Modified verification logic with higher priority for blink
            static_score = depth_verified
            dynamic_score = movement_detected or rotation_detected or micro_movements_verified

            # Final verification requires adjusted logic
            liveness_verified = (
                    (blink_detected or total_blinks >= 1) and  # Even 1 blink is acceptable
                    (static_score * FUSION_WEIGHTS['static'] +
                     dynamic_score * FUSION_WEIGHTS['dynamic'] >= 0.4)  # Reduced from 0.5
                    and verification_score >= 0.5  # Reduced from 0.6
            )
        except Exception as e:
            print(f"Error in verification calculation: {str(e)}")
            liveness_verified = False
            verification_score = 0

        # Report results
        if not liveness_verified:
            print("Liveness verification failed:")
            if not blink_detected:
                print(f"- CRITICAL: Blink verification failed: {total_blinks}/{BLINK_TOTAL_REQUIRED} blinks detected")

            # Only report depth verification if we have valid data
            if not depth_verified and depth_variance > 0:
                print(
                    f"- Depth verification failed: {depth_variance:.1f}/{DEPTH_VARIANCE_THRESHOLD} variance, {depth_range:.1f}/{DEPTH_RANGE_THRESHOLD}mm range")
            elif not depth_verified:
                print("- Depth verification failed: insufficient depth data")

            if not movement_detected and not rotation_detected:
                print("- Movement verification failed: insufficient head movement detected")
            if not micro_movements_verified:
                print("- Micro-movement verification failed: unnatural movement patterns")
            if not texture_verified:
                print("- Texture analysis failed: possible screen/replay attack")

            print(f"- Overall verification score: {verification_score:.2f}/0.5 required")
            return False

        print("Liveness verified! Proceeding with face recognition...")

        # Now proceed with face recognition since liveness is verified
        if face is not None:
            try:
                test_features = extract_features(face)
                similarity = 1 - cosine(registered_features, test_features)

                if similarity > 0.60:  # Adjust threshold based on testing
                    print(f"Face recognized with similarity: {similarity:.2f}")
                    return True
                else:
                    print(f"Face not recognized. Similarity: {similarity:.2f}")
                    return False
            except Exception as e:
                print(f"Error in face recognition: {str(e)}")
                return False
        else:
            print("Face not detected in the recognition image.")
            return False

    except Exception as e:
        # Make sure to release resources even if an exception occurs
        cap.release()
        cv2.destroyAllWindows()
        print(f"Unexpected error in face recognition: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def recognize_face_web(registered_features):
    """
    Modified version of recognize_face that works with web-based face recognition
    by using MonkeyPatching to override VideoCapture with a custom implementation
    that uses the frames sent from the browser.
    """
    # This will be set from the outside when calling this function
    global web_frames
    global current_frame_index

    # Initialize variables (same as in original recognize_face)
    ear_values = []
    blink_frames = 0
    total_blinks = 0
    movement_frames = 0
    blink_detected = False
    movement_detected = False
    rotation_detected = False
    depth_verified = False
    texture_verified = False
    micro_movements_verified = False
    in_blink = False

    # Initialize variables for error reporting
    depth_variance = 0.0
    depth_range = 0.0
    verification_score = 0.0
    face = None

    # Use the same parameters as in the original recognize_face
    BLINK_CONSEC_FRAMES = 1
    BLINK_TOTAL_REQUIRED = 2
    DEPTH_VARIANCE_THRESHOLD = 800.0
    DEPTH_RANGE_THRESHOLD = 30.0
    MOVEMENT_THRESHOLD = 0.35
    MOVEMENT_FRAMES_REQUIRED = 8
    ROTATION_THRESHOLD = 4.0

    # History of data for temporal analysis
    prev_landmarks = None
    landmarks_history = []
    frame_history = []
    pitch_yaw_history = []

    # Verification scores for weighted fusion
    scores = {'blink': 0, 'depth': 0, 'dynamic': 0, 'texture': 0}

    print("Looking for face... Please blink naturally and move your head slightly for verification.")

    # Custom VideoCapture class that serves frames from web_frames
    class WebVideoCapture:
        def __init__(self, _):
            self.index = 0

        def isOpened(self):
            return True

        def read(self):
            global web_frames, current_frame_index
            if current_frame_index < len(web_frames):
                frame = web_frames[current_frame_index]
                current_frame_index += 1
                return True, frame
            return False, None

        def release(self):
            pass

    # Save the original VideoCapture
    original_video_capture = cv2.VideoCapture

    try:
        # Replace VideoCapture with our custom implementation
        cv2.VideoCapture = WebVideoCapture

        # Main processing (simplified from recognize_face)
        cap = cv2.VideoCapture(0)  # The parameter doesn't matter

        # Main processing loop
        while True:
            ret, frame = cap.read()
            if not ret:
                print("End of frames")
                break

            # Store frame for temporal analysis
            frame_history.append(frame.copy())
            if len(frame_history) > 20:
                frame_history.pop(0)

            # Get adaptive lighting threshold
            EAR_THRESHOLD = get_adaptive_ear_threshold(frame)

            # Detect face and landmarks
            try:
                face, eye_landmarks, face_box, depth_points, landmarks_3d = detect_face(frame)
            except Exception as e:
                print(f"Error in face detection: {str(e)}")
                continue

            if face is not None and eye_landmarks is not None and depth_points is not None:
                left_eye, right_eye = eye_landmarks

                # Calculate EAR for both eyes
                left_ear = calculate_ear(left_eye)
                right_ear = calculate_ear(right_eye)

                # Average EAR
                ear = (left_ear + right_ear) / 2.0
                ear_values.append(ear)

                # Smooth EAR to reduce noise
                if len(ear_values) > 3:
                    ear = np.mean(ear_values[-3:])

                # Store landmarks history for movement analysis
                landmarks_history.append(landmarks_3d)
                if len(landmarks_history) > 30:
                    landmarks_history.pop(0)

                # Analyze depth for flat surface detection
                try:
                    depth_variance, depth_range = analyze_depth(depth_points)
                    if depth_variance > DEPTH_VARIANCE_THRESHOLD and depth_range > DEPTH_RANGE_THRESHOLD:
                        depth_verified = True
                        scores['depth'] = min(1.0, depth_variance / DEPTH_VARIANCE_THRESHOLD * 0.8)
                except Exception as e:
                    print(f"Error analyzing depth: {str(e)}")

                # Detect head movement with rotation analysis
                try:
                    is_moving, movement_amount, (pitch, yaw) = detect_head_movement(
                        landmarks_3d, prev_landmarks, MOVEMENT_THRESHOLD)

                    # Store pitch/yaw for rotation analysis
                    pitch_yaw_history.append((pitch, yaw))
                    if len(pitch_yaw_history) > 10:
                        pitch_yaw_history.pop(0)

                    # Check for significant rotation
                    if len(pitch_yaw_history) >= 5:
                        max_pitch = max([abs(p) for p, _ in pitch_yaw_history])
                        max_yaw = max([abs(y) for _, y in pitch_yaw_history])
                        if max_pitch > ROTATION_THRESHOLD or max_yaw > ROTATION_THRESHOLD:
                            rotation_detected = True

                    if is_moving:
                        movement_frames += 1
                    else:
                        movement_frames = max(0, movement_frames - 1)

                    if movement_frames >= MOVEMENT_FRAMES_REQUIRED:
                        movement_detected = True
                        scores['dynamic'] = min(1.0, movement_frames / MOVEMENT_FRAMES_REQUIRED * 0.9)
                except Exception as e:
                    print(f"Error detecting head movement: {str(e)}")

                # Update previous landmarks
                prev_landmarks = landmarks_3d

                # Detect micro-movements
                if len(landmarks_history) > 10:
                    try:
                        is_natural, micro_var = detect_micro_movements(landmarks_history, frames=8)
                        if is_natural:
                            micro_movements_verified = True
                            scores['dynamic'] = max(scores['dynamic'], min(1.0, micro_var / 5.0 * 0.7))
                    except Exception as e:
                        print(f"Error detecting micro-movements: {str(e)}")

                # Texture analysis for replay detection
                if len(frame_history) > 10 and len(ear_values) % 5 == 0:
                    try:
                        is_real_face, (entropy, uniformity) = analyze_texture_lbp(face)
                        if is_real_face:
                            texture_verified = True
                            scores['texture'] = min(1.0, entropy / 6.0 * 0.8)
                    except Exception as e:
                        print(f"Error in texture analysis: {str(e)}")

                # Track blinks
                if len(ear_values) > 5:
                    # Calculate baseline EAR for this person
                    if len(ear_values) > 20:
                        baseline_ear = np.mean(sorted(ear_values[-20:])[-10:])
                    else:
                        baseline_ear = np.mean(sorted(ear_values)[-int(len(ear_values) / 2):])

                    # Calculate relative threshold
                    ear_multiplier = 0.90 if baseline_ear > 0.4 else 0.85
                    personal_threshold = baseline_ear * ear_multiplier

                    recent_min_ear = min(ear_values[-5:])
                    recent_max_ear = max(ear_values[-5:])

                    min_ear_change_ratio = 0.05 if baseline_ear > 0.4 else 0.1
                    ear_change_ratio = (recent_max_ear - recent_min_ear) / recent_max_ear

                    # Blink detection
                    if (ear_change_ratio > min_ear_change_ratio or
                        (recent_max_ear - ear) > 0.02) and not in_blink and ear < personal_threshold:
                        blink_frames += 1
                        if blink_frames >= BLINK_CONSEC_FRAMES:
                            in_blink = True
                            print("BLINK STARTING")
                    elif in_blink and ear > (personal_threshold * 1.02):
                        in_blink = False
                        total_blinks += 1
                        blink_frames = 0
                        print(f"BLINK DETECTED! Total: {total_blinks}/{BLINK_TOTAL_REQUIRED}")

                # Check if we have enough blinks
                if total_blinks >= BLINK_TOTAL_REQUIRED:
                    blink_detected = True
                    scores['blink'] = 1.0
                elif total_blinks > 0:
                    scores['blink'] = 0.7

        # Calculate verification
        verification_score = (
                VALIDATION_WEIGHTS['blink'] * scores['blink'] +
                VALIDATION_WEIGHTS['depth'] * scores['depth'] +
                VALIDATION_WEIGHTS['dynamic'] * scores['dynamic'] +
                VALIDATION_WEIGHTS['texture'] * scores['texture']
        )

        static_score = depth_verified
        dynamic_score = movement_detected or rotation_detected or micro_movements_verified

        # Final verification
        liveness_verified = (
                (blink_detected or total_blinks >= 1) and
                (static_score * FUSION_WEIGHTS['static'] +
                 dynamic_score * FUSION_WEIGHTS['dynamic'] >= 0.4) and
                verification_score >= 0.5
        )

        # Print verification status
        print(f"Blinks detected: {total_blinks}/{BLINK_TOTAL_REQUIRED}")
        print(f"Depth verified: {depth_verified}")
        print(f"Movement detected: {movement_detected}")
        print(f"Rotation detected: {rotation_detected}")
        print(f"Micro-movements verified: {micro_movements_verified}")
        print(f"Texture verified: {texture_verified}")
        print(f"Verification score: {verification_score:.2f}")
        print(f"Liveness verified: {liveness_verified}")

        # Face recognition if liveness verified
        if liveness_verified and face is not None:
            try:
                test_features = extract_features(face)
                similarity = 1 - cosine(registered_features, test_features)

                if similarity > 0.60:
                    print(f"Face recognized with similarity: {similarity:.2f}")
                    return True
                else:
                    print(f"Face not recognized. Similarity: {similarity:.2f}")
                    return False
            except Exception as e:
                print(f"Error in face recognition: {str(e)}")
                return False
        else:
            print("Liveness verification failed")
            return False

    except Exception as e:
        print(f"Unexpected error in face recognition: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore the original VideoCapture
        cv2.VideoCapture = original_video_capture

# Main execution flow
if __name__ == "__main__":
    try:
        # Step 1: Register student's face from webcam
        student_features = register_student()

        # Step 2: Recognize the captured face using the webcam with anti-spoofing
        if student_features is not None:
            recognize_face(student_features)
        else:
            print("Registration failed. Please try again.")
    except Exception as e:
        print(f"Critical error in main program: {str(e)}")
        import traceback
        traceback.print_exc()