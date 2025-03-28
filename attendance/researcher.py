import cv2
import numpy as np
import time
import mediapipe as mp
from keras_facenet import FaceNet
from sklearn.preprocessing import normalize
from scipy.spatial.distance import cosine
from scipy.spatial import distance as dist
import math

# Add PyTorch imports for FasterRCNN
import torch
import torchvision
from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor


# UI Enhancement with dynamic text sizing
def get_dynamic_font_size(frame_width, frame_height, base_size=0.7, min_size=0.4, max_size=1.2):
    """
    Calculate dynamic font size based on frame dimensions

    Parameters:
    frame_width (int): Width of the frame
    frame_height (int): Height of the frame
    base_size (float): Base font size
    min_size (float): Minimum font size
    max_size (float): Maximum font size

    Returns:
    float: Calculated font size
    """
    # Calculate a scale factor based on the frame dimensions
    scale_factor = min(frame_width, frame_height) / 1000.0

    # Apply the scale factor to the base size
    font_size = base_size * scale_factor

    # Ensure the font size is within the specified range
    return max(min_size, min(font_size, max_size))


# UI Enhancement Functions
def create_enhanced_ui(frame, results_dict, ear_values=None, ear_threshold=0.22):
    """
    Create an enhanced UI layout for the face recognition system with dynamic sizing

    Parameters:
    frame (numpy.ndarray): The current video frame
    results_dict (dict): Dictionary containing all detection results
    ear_values (list, optional): History of EAR values for plotting
    ear_threshold (float, optional): Current EAR threshold

    Returns:
    numpy.ndarray: The enhanced UI frame
    """
    # Extract values from results dictionary
    face_box = results_dict.get('face_box', None)
    ear = results_dict.get('ear', 0)
    baseline_ear = results_dict.get('baseline_ear', 0)
    personal_threshold = results_dict.get('personal_threshold', 0)
    total_blinks = results_dict.get('total_blinks', 0)
    blinks_required = results_dict.get('blinks_required', 2)
    depth_variance = results_dict.get('depth_variance', 0)
    depth_range = results_dict.get('depth_range', 0)
    movement_amount = results_dict.get('movement_amount', 0)
    pitch = results_dict.get('pitch', 0)
    yaw = results_dict.get('yaw', 0)
    verification_score = results_dict.get('verification_score', 0)
    remaining_time = results_dict.get('remaining_time', 30)
    landmarks_3d = results_dict.get('landmarks_3d', None)

    # Verification status
    blink_verified = results_dict.get('blink_verified', False)
    depth_verified = results_dict.get('depth_verified', False)
    movement_verified = results_dict.get('movement_verified', False)
    rotation_verified = results_dict.get('rotation_verified', False)
    micro_movements_verified = results_dict.get('micro_movements_verified', False)
    final_verification = results_dict.get('final_verification', False)

    # Create a copy of the frame for drawing
    h, w = frame.shape[:2]

    # Calculate dynamic font sizes
    title_font_size = get_dynamic_font_size(w, h, base_size=0.8, min_size=0.6, max_size=1.0)
    section_font_size = get_dynamic_font_size(w, h, base_size=0.7, min_size=0.5, max_size=0.9)
    item_font_size = get_dynamic_font_size(w, h, base_size=0.6, min_size=0.4, max_size=0.8)
    small_font_size = get_dynamic_font_size(w, h, base_size=0.5, min_size=0.3, max_size=0.7)

    # Calculate panel width based on frame width
    panel_width = max(300, min(500, int(w * 0.5)))  # Dynamic panel width

    # Create a larger canvas to accommodate the UI panels
    canvas_width = w + panel_width
    canvas_height = h
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    # Add frame to the canvas
    canvas[0:h, 0:w] = frame

    # Draw facial landmarks if available
    if landmarks_3d is not None:
        # Convert 3D landmarks to 2D points for drawing
        for point in landmarks_3d:
            x, y = int(point[0]), int(point[1])
            if 0 <= x < w and 0 <= y < h:  # Ensure point is within frame boundaries
                cv2.circle(canvas, (x, y), 1, (0, 255, 0), -1)

    # Draw face box if available
    if face_box is not None:
        x, y, w_box, h_box = face_box
        cv2.rectangle(canvas, (x, y), (x + w_box, y + h_box), (0, 255, 0), 2)

    # Create right panel with white background
    panel_x = w
    canvas[:, panel_x:panel_x + panel_width] = [240, 240, 240]  # Light gray background

    # Add title bar
    title_height = int(h * 0.07)  # Dynamic title height
    cv2.rectangle(canvas, (panel_x, 0), (panel_x + panel_width, title_height), (70, 70, 70), -1)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(canvas, "LIVENESS DETECTION SYSTEM",
                (panel_x + 10, title_height - 15),
                font, title_font_size, (240, 240, 240), 2)

    # Draw verification score as a progress bar
    score_y = title_height + int(h * 0.07)
    cv2.putText(canvas, f"Verification Score: {verification_score:.2f}",
                (panel_x + 10, score_y - 15), font, item_font_size, (0, 0, 0), 1)

    # Draw the background bar
    bar_length = panel_width - 20
    bar_height = max(15, int(h * 0.02))
    cv2.rectangle(canvas, (panel_x + 10, score_y),
                  (panel_x + 10 + bar_length, score_y + bar_height),
                  (200, 200, 200), -1)

    # Draw the filled portion of the bar
    filled_length = int(bar_length * min(1.0, verification_score))

    # Color based on score
    if verification_score >= 0.8:
        bar_color = (0, 200, 0)  # Green
    elif verification_score >= 0.5:
        bar_color = (0, 200, 200)  # Yellow-green
    else:
        bar_color = (0, 100, 200)  # Orange-red

    cv2.rectangle(canvas, (panel_x + 10, score_y),
                  (panel_x + 10 + filled_length, score_y + bar_height),
                  bar_color, -1)

    # Add threshold markers
    threshold_x = panel_x + 10 + int(bar_length * 0.5)
    cv2.line(canvas, (threshold_x, score_y - 5), (threshold_x, score_y + bar_height + 5), (0, 0, 0), 2)
    cv2.putText(canvas, "Threshold",
                (threshold_x - 40, score_y + bar_height + 20),
                font, small_font_size, (0, 0, 0), 1)

    # Section for verification status - dynamic positioning with enhanced visibility
    section_spacing = int(h * 0.04)  # Space between sections
    status_y = score_y + section_spacing * 2

    # Add background for section header to improve readability
    text_size = cv2.getTextSize("VERIFICATION STATUS", font, section_font_size, 2)[0]
    header_bg = np.ones((text_size[1] + 10, text_size[0] + 20, 3), dtype=np.uint8) * 240
    header_bg[:, :, 0] = 220  # Add slight blue tint to background
    header_bg[:, :, 1] = 230

    # Place background on canvas
    bg_y_start = status_y - text_size[1] - 5
    bg_y_end = status_y + 5
    bg_x_start = panel_x + 5
    bg_x_end = panel_x + 5 + text_size[0] + 20

    if (bg_y_start >= 0 and bg_y_end < canvas.shape[0] and
            bg_x_start >= 0 and bg_x_end < canvas.shape[1]):
        canvas[bg_y_start:bg_y_end, bg_x_start:bg_x_end] = header_bg

    # Draw section header with enhanced visibility
    cv2.putText(canvas, "VERIFICATION STATUS",
                (panel_x + 15, status_y), font, section_font_size, (0, 0, 0), 2)

    # Draw verification icons with improved spacing and sizing
    icon_size = max(20, int(h * 0.03))  # Slightly larger icons
    spacing = max(35, int(h * 0.05))  # Increased spacing
    icon_x = panel_x + 20
    y_pos = status_y + spacing

    # Blink verification (primary)
    status_color = (0, 200, 0) if blink_verified else (0, 0, 200)
    status_marker = "✓" if blink_verified else "×"
    cv2.rectangle(canvas, (icon_x, y_pos - icon_size), (icon_x + icon_size, y_pos),
                  status_color, -1)
    cv2.putText(canvas, status_marker, (icon_x + 5, y_pos - 5), font, item_font_size, (255, 255, 255), 2)
    cv2.putText(canvas, f"Blink Detection: {total_blinks}/{blinks_required} (PRIMARY)",
                (icon_x + icon_size + 10, y_pos - 5), font, item_font_size, (0, 0, 0), 1)

    # Depth verification
    y_pos += spacing
    status_color = (0, 200, 0) if depth_verified else (0, 0, 200)
    status_marker = "✓" if depth_verified else "×"
    cv2.rectangle(canvas, (icon_x, y_pos - icon_size), (icon_x + icon_size, y_pos),
                  status_color, -1)
    cv2.putText(canvas, status_marker, (icon_x + 5, y_pos - 5), font, item_font_size, (255, 255, 255), 2)
    cv2.putText(canvas, "Depth Verification",
                (icon_x + icon_size + 10, y_pos - 5), font, item_font_size, (0, 0, 0), 1)

    # Movement verification
    y_pos += spacing
    movement_text = "Movement & Rotation" if (movement_verified and rotation_verified) else \
        "Movement" if movement_verified else \
            "Rotation" if rotation_verified else \
                "Movement Verification"
    status_color = (0, 200, 0) if (movement_verified or rotation_verified) else (0, 0, 200)
    status_marker = "✓" if (movement_verified or rotation_verified) else "×"
    cv2.rectangle(canvas, (icon_x, y_pos - icon_size), (icon_x + icon_size, y_pos),
                  status_color, -1)
    cv2.putText(canvas, status_marker, (icon_x + 5, y_pos - 5), font, item_font_size, (255, 255, 255), 2)
    cv2.putText(canvas, movement_text,
                (icon_x + icon_size + 10, y_pos - 5), font, item_font_size, (0, 0, 0), 1)

    # Micro-movements verification
    y_pos += spacing
    status_color = (0, 200, 0) if micro_movements_verified else (0, 0, 200)
    status_marker = "✓" if micro_movements_verified else "×"
    cv2.rectangle(canvas, (icon_x, y_pos - icon_size), (icon_x + icon_size, y_pos),
                  status_color, -1)
    cv2.putText(canvas, status_marker, (icon_x + 5, y_pos - 5), font, item_font_size, (255, 255, 255), 2)
    cv2.putText(canvas, "Micro-movements",
                (icon_x + icon_size + 10, y_pos - 5), font, item_font_size, (0, 0, 0), 1)

    # Draw metrics section - dynamic positioning
    metrics_y = y_pos + int(h * 0.08)
    cv2.putText(canvas, "DETAILED METRICS",
                (panel_x + 10, metrics_y), font, section_font_size, (0, 0, 0), 2)

    # Function to draw a metric with label and value
    def draw_metric(label, value, y_position, unit="", color=(0, 0, 0)):
        cv2.putText(canvas, label, (panel_x + 20, y_position), font, small_font_size, color, 1)
        value_x = panel_x + int(panel_width * 0.6)  # Dynamic positioning
        cv2.putText(canvas, f"{value}{unit}", (value_x, y_position), font, small_font_size, color, 1)

    # Draw metrics
    metric_spacing = max(20, int(h * 0.035))
    m_y = metrics_y + int(h * 0.05)
    draw_metric("Eye Aspect Ratio (EAR):", f"{ear:.2f}", m_y)
    m_y += metric_spacing
    draw_metric("Personal EAR Threshold:", f"{personal_threshold:.2f}", m_y)
    m_y += metric_spacing
    draw_metric("Depth Variance:", f"{depth_variance:.1f}", m_y)
    m_y += metric_spacing
    draw_metric("Depth Range:", f"{depth_range:.1f}", m_y, "mm")
    m_y += metric_spacing
    draw_metric("Movement Magnitude:", f"{movement_amount:.2f}", m_y)
    m_y += metric_spacing
    draw_metric("Head Rotation:", f"P:{pitch:.1f}° Y:{yaw:.1f}°", m_y)

    # Draw final status and timer - dynamic positioning
    final_y = canvas_height - int(h * 0.12)
    if final_verification:
        cv2.rectangle(canvas, (panel_x, final_y - 50), (panel_x + panel_width, final_y + 30), (0, 200, 0), -1)
        cv2.putText(canvas, "LIVENESS VERIFIED",
                    (panel_x + int(panel_width * 0.15), final_y - 10),
                    font, section_font_size, (255, 255, 255), 2)
    else:
        # Timer bar
        cv2.putText(canvas, f"Time Remaining: {remaining_time}s",
                    (panel_x + 20, final_y - 10), font, item_font_size, (0, 0, 0), 1)

        # Draw timer bar
        bar_width = panel_width - 40
        bar_height = max(15, int(h * 0.02))
        cv2.rectangle(canvas, (panel_x + 20, final_y + 10),
                      (panel_x + 20 + bar_width, final_y + 10 + bar_height),
                      (200, 200, 200), -1)

        # Fill with remaining time (assuming 30 second timeout)
        fill_width = int(bar_width * (remaining_time / 30.0))
        cv2.rectangle(canvas, (panel_x + 20, final_y + 10),
                      (panel_x + 20 + fill_width, final_y + 10 + bar_height),
                      (0, 128, 255), -1)

    # Draw EAR graph if values are provided
    if ear_values is not None and len(ear_values) > 0:
        graph_height = int(h * 0.25)
        graph_width = panel_width - 20
        graph_y = final_y - int(h * 0.05)

        # Draw graph background
        cv2.rectangle(canvas, (panel_x + 10, graph_y - graph_height - 10),
                      (panel_x + 10 + graph_width, graph_y + 10),
                      (255, 255, 255), -1)
        cv2.rectangle(canvas, (panel_x + 10, graph_y - graph_height - 10),
                      (panel_x + 10 + graph_width, graph_y + 10),
                      (0, 0, 0), 1)

        # Draw graph title
        cv2.putText(canvas, "EAR VALUES OVER TIME",
                    (panel_x + 20, graph_y - graph_height - 20), font, small_font_size, (0, 0, 0), 1)

        # Draw horizontal grid lines with improved scale
        # Dynamically determine appropriate y-axis scale based on EAR values
        if ear_values and len(ear_values) > 5:
            y_max = min(0.45, max(ear_values) * 1.2)  # Scale the max value
            y_min = max(0.05, min(ear_values) * 0.8)  # Scale the min value
        else:
            y_max = 0.45
            y_min = 0.05

        y_range = y_max - y_min

        # Draw y-axis grid lines with clear labeling
        for i in range(5):
            # Calculate the actual value at this grid line
            value = y_min + (i * y_range / 4)
            # Calculate the y-position
            y_level = graph_y - int(((value - y_min) / y_range) * graph_height)

            # Draw the grid line
            cv2.line(canvas, (panel_x + 10, y_level),
                     (panel_x + 10 + graph_width, y_level),
                     (200, 200, 200), 1)

            # Label the grid lines with actual values
            cv2.putText(canvas, f"{value:.2f}",
                        (panel_x, y_level + 5), font, small_font_size * 0.8, (0, 0, 0), 1)

        # Draw the EAR threshold line with enhanced visibility
        threshold_y = graph_y - int(((ear_threshold - y_min) / y_range) * graph_height)
        cv2.line(canvas, (panel_x + 10, threshold_y),
                 (panel_x + 10 + graph_width, threshold_y),
                 (0, 0, 255), 2)  # Pure blue for better visibility

        # Add a background rectangle for the threshold label to improve readability
        text_size = cv2.getTextSize("Threshold", font, small_font_size * 0.8, 1)[0]
        cv2.rectangle(canvas,
                      (panel_x + 15, threshold_y - text_size[1] - 5),
                      (panel_x + 15 + text_size[0], threshold_y + 5),
                      (255, 255, 255), -1)  # White background

        cv2.putText(canvas, "Threshold",
                    (panel_x + 15, threshold_y - 5), font, small_font_size * 0.8, (0, 0, 255), 1)

        # Plot the EAR values with smoothed line and better visualization
        if len(ear_values) > 1:
            # Only use the last 100 values at most
            plot_values = ear_values[-100:] if len(ear_values) > 100 else ear_values

            # Apply smoothing to the plot values for better visualization
            if len(plot_values) >= 5:
                smoothed_values = []
                window_size = 3  # Must be odd
                half_window = window_size // 2

                # Apply moving average smoothing
                for i in range(len(plot_values)):
                    if i < half_window:
                        # Start of array - fewer points to average
                        smoothed_values.append(sum(plot_values[:i + half_window + 1]) / (i + half_window + 1))
                    elif i >= len(plot_values) - half_window:
                        # End of array - fewer points to average
                        smoothed_values.append(
                            sum(plot_values[i - half_window:]) / (len(plot_values) - i + half_window))
                    else:
                        # Middle of array - full window
                        smoothed_values.append(sum(plot_values[i - half_window:i + half_window + 1]) / window_size)
            else:
                smoothed_values = plot_values

            points = []

            # Use smoothed values for plotting
            for i, val in enumerate(smoothed_values):
                x = panel_x + 10 + int(i * graph_width / len(smoothed_values))
                # Scale to fit 0.0 to 0.4 range
                y = graph_y - int((min(val, 0.4) / 0.4) * graph_height)
                points.append((x, y))

            # Draw the EAR line with thicker stroke for better visibility
            for i in range(len(points) - 1):
                cv2.line(canvas, points[i], points[i + 1], (0, 200, 0), 2)

            # Highlight detected blinks on the graph
            # This helps visualize where blinks were detected
            if 'blink_timestamps' in results_dict and results_dict['blink_timestamps']:
                for blink_idx in results_dict['blink_timestamps']:
                    if blink_idx < len(smoothed_values):
                        blink_x = panel_x + 10 + int(blink_idx * graph_width / len(smoothed_values))
                        # Draw a circle at the blink point
                        cv2.circle(canvas,
                                   (
                                   blink_x, graph_y - int((min(smoothed_values[blink_idx], 0.4) / 0.4) * graph_height)),
                                   5, (255, 0, 255), -1)

    return canvas


def integrate_improved_ui(frame, ear_values, ear_threshold, face_box, eye_landmarks,
                          depth_verified, depth_variance, depth_range,
                          movement_detected, rotation_detected, movement_amount, pitch, yaw,
                          micro_movements_verified, blink_detected,
                          total_blinks, blinks_required, verification_score,
                          final_verification, landmarks_3d=None, remaining_time=30,
                          personal_threshold=0.22, baseline_ear=0.25, ear=0.24,
                          blink_timestamps=None):
    """
    Wrapper function to integrate the improved UI with your existing code
    """
    # Create results dictionary with added blink timestamps for graph visualization
    results = {
        'face_box': face_box,
        'ear': ear,
        'baseline_ear': baseline_ear,
        'personal_threshold': personal_threshold,
        'total_blinks': total_blinks,
        'blinks_required': blinks_required,
        'depth_variance': depth_variance,
        'depth_range': depth_range,
        'movement_amount': movement_amount,
        'pitch': pitch,
        'yaw': yaw,
        'verification_score': verification_score,
        'remaining_time': remaining_time,
        'blink_verified': blink_detected,
        'depth_verified': depth_verified,
        'movement_verified': movement_detected,
        'rotation_verified': rotation_detected,
        'micro_movements_verified': micro_movements_verified,
        'final_verification': final_verification,
        'landmarks_3d': landmarks_3d,
        'blink_timestamps': blink_timestamps
    }

    # Create enhanced UI
    display_frame = create_enhanced_ui(frame, results, ear_values, ear_threshold)

    return display_frame


# Initialize the FaceNet embedder
embedder = FaceNet()

# Initialize MediaPipe Face Mesh for landmark detection
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    static_image_mode=False
)


# Function to load the FasterRCNN model
def load_fasterrcnn_model(model_path=None):
    """Load the trained FasterRCNN-MobileNet model for face detection"""
    try:
        # Use path relative to the current script
        if model_path is None:
            import os
            # Get the directory where this script is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "checkpoint.pth")

        print(f"Loading model from: {model_path}")

        # Initialize the model architecture
        model = fasterrcnn_mobilenet_v3_large_fpn(weights=None)
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_channels=in_features, num_classes=2)  # background and face

        # Load the trained weights
        model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=False))
        model.eval()  # Set to evaluation mode
        print("FasterRCNN-MobileNet model loaded successfully")
        return model
    except Exception as e:
        print(f"Error loading FasterRCNN model: {str(e)}")
        print("Falling back to MediaPipe for face detection")
        return None


# Initialize FasterRCNN model for face detection
try:
    face_detector = load_fasterrcnn_model()
    print("Loaded fasterrcnn_model")
except Exception as e:
    print(f"Failed to initialize FasterRCNN model: {str(e)}")
    face_detector = None

# MediaPipe indices for the left and right eyes
LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]

# Key facial landmarks for depth analysis
DEPTH_LANDMARKS = [1, 4, 152, 234, 454]

# Fusion weights heavily prioritizing blink detection for research setting
FUSION_WEIGHTS = {
    'static': 0.5,  # EAR/depth reduced slightly
    'dynamic': 0.5  # Increased to balance verification
}

# Adjust validation weights to strongly prioritize blink detection for research
VALIDATION_WEIGHTS = {
    'blink': 0.7,  # Heavily increased for research focus on blink detection
    'depth': 0.15,  # Reduced importance
    'dynamic': 0.15  # Maintained
}


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


# Calculate Eye Aspect Ratio (EAR) with improved accuracy
def calculate_ear(eye_landmarks):
    # Calculate the vertical distances
    A = dist.euclidean(eye_landmarks[1], eye_landmarks[4])
    B = dist.euclidean(eye_landmarks[2], eye_landmarks[5])

    # Calculate the horizontal distance
    C = dist.euclidean(eye_landmarks[0], eye_landmarks[3])

    # Calculate the eye aspect ratio
    # Add small epsilon to prevent division by zero
    ear = (A + B) / (2.0 * C + 1e-6)

    # Clip extreme values that might be due to detection errors
    ear = max(0.1, min(ear, 0.5))

    return ear


# Detect face and extract face area - Updated to use FasterRCNN with MediaPipe fallback
def detect_face(frame):
    """
    Detect face using FasterRCNN model and extract landmarks using MediaPipe

    Returns:
        face_area: The cropped face image
        eye_landmarks: Left and right eye landmarks for EAR calculation
        face_box: The bounding box of the face
        depth_points: 3D landmarks for depth analysis
        landmarks_3d: All 3D facial landmarks
    """
    h, w, _ = frame.shape

    # Try using FasterRCNN if available
    if face_detector is not None:
        try:
            # Convert to tensor for FasterRCNN
            img_tensor = torch.tensor(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).permute(2, 0, 1).float() / 255.0

            # Get predictions from FasterRCNN
            with torch.no_grad():
                prediction = face_detector([img_tensor])[0]

            # Filter predictions with confidence threshold
            threshold = 0.35  # Same threshold as in the FasterRCNN config
            indices = prediction["scores"] >= threshold
            boxes = prediction["boxes"][indices]
            scores = prediction["scores"][indices]

            if len(boxes) > 0:
                # Get the highest confidence face
                best_idx = torch.argmax(scores)
                box = boxes[best_idx].int().cpu().numpy().tolist()

                # Extract face area with padding
                x_min, y_min, x_max, y_max = box
                padding = 20
                x_min = max(0, x_min - padding)
                y_min = max(0, y_min - padding)
                x_max = min(w, x_max + padding)
                y_max = min(h, y_max + padding)

                # Make sure we have valid face area before extraction
                if x_min < x_max and y_min < y_max:
                    face_area = frame[y_min:y_max, x_min:x_max]
                    face_box = (x_min, y_min, x_max - x_min, y_max - y_min)

                    # We still need MediaPipe for landmarks
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(rgb_frame)

                    if results.multi_face_landmarks:
                        # Get the facial landmarks from MediaPipe
                        face_landmarks = results.multi_face_landmarks[0]

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

                        return face_area, (left_eye, right_eye), face_box, depth_points, landmarks_3d
                    else:
                        # FasterRCNN found a face, but MediaPipe couldn't find landmarks
                        return face_area, None, face_box, None, None
        except Exception as e:
            print(f"FasterRCNN detection error: {str(e)}. Falling back to MediaPipe.")

    # Fallback to original MediaPipe method if FasterRCNN fails or isn't available
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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

    return None, None, None, None, None


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


# Adaptive lighting-based EAR threshold with improved sensitivity
def get_adaptive_ear_threshold(frame, ear_history=None):
    # Calculate average brightness of the frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)

    # If we have ear history, make threshold more adaptive based on actual measurements
    if ear_history and len(ear_history) > 10:
        # Sort EAR values and get median for more stable threshold calculation
        sorted_ears = sorted(ear_history[-20:])
        median_ear = sorted_ears[len(sorted_ears) // 2]

        # Take 85-90% of median as threshold (more sensitive)
        base_threshold = median_ear * 0.85

        # Adjust for lighting as a fine-tuning step
        if brightness < 80:  # Low light
            return max(0.15, base_threshold * 0.95)  # More sensitive in low light
        elif brightness > 200:  # Very bright light
            return max(0.17, base_threshold * 1.05)  # Less sensitive in bright light
        else:  # Normal lighting
            return max(0.16, base_threshold)
    else:
        # Default thresholds when not enough history
        if brightness < 80:  # Low light
            return 0.17
        elif brightness > 200:  # Very bright light
            return 0.24
        else:  # Normal lighting
            return 0.20  # More sensitive default threshold


# Register a student's face
def register_student():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam. Check your camera connection.")
            return None

        print("Press 'q' to capture student's face for registration.")

        # Create a named window with adjustable size
        cv2.namedWindow("Face Registration", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Face Registration", 800, 700)  # Adjust dimensions to fit your screen

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame. Check your camera.")
                break

            # Create simple UI for registration
            h, w = frame.shape[:2]
            info_bar = np.zeros((100, w, 3), dtype=np.uint8)
            info_bar[:] = (70, 70, 70)  # Dark gray background

            # Add text with dynamic font size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_size = get_dynamic_font_size(w, h, base_size=1.0, min_size=0.7, max_size=1.2)
            cv2.putText(info_bar, "FACE REGISTRATION", (20, 40), font, font_size, (255, 255, 255), 2)

            small_font_size = get_dynamic_font_size(w, h, base_size=0.7, min_size=0.5, max_size=0.9)
            cv2.putText(info_bar, "Position your face in the center and press 'q' to capture",
                        (20, 80), font, small_font_size, (255, 255, 255), 1)

            # Combine with frame
            display = np.vstack((info_bar, frame))

            # Try to detect face and draw landmarks for visual feedback
            face, eye_landmarks, face_box, _, landmarks_3d = detect_face(frame)

            # If landmarks are detected, draw them on the display
            if landmarks_3d is not None:
                for point in landmarks_3d:
                    x, y = int(point[0]), int(point[1] + 100)  # +100 to adjust for info_bar
                    if 0 <= x < w and 100 <= y < h + 100:  # Ensure point is within display boundaries
                        cv2.circle(display, (x, y), 1, (0, 255, 0), -1)

                # Draw face box if available
                if face_box is not None:
                    x, y, w_box, h_box = face_box
                    cv2.rectangle(display, (x, y + 100), (x + w_box, y + h_box + 100), (0, 255, 0), 2)

            cv2.imshow("Face Registration", display)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Process the final frame for registration
        face, _, _, _, _ = detect_face(frame)

        cap.release()
        cv2.destroyAllWindows()

        if face is not None:
            features = extract_features(face)

            # Show confirmation screen
            confirmation = np.zeros((300, 400, 3), dtype=np.uint8)
            confirmation[:] = (240, 240, 240)  # Light gray background

            # Display the captured face
            face_resized = cv2.resize(face, (200, 200))
            confirmation[50:250, 100:300] = face_resized

            # Add confirmation text with dynamic font size
            font_size = get_dynamic_font_size(400, 300, base_size=0.8, min_size=0.6, max_size=1.0)
            cv2.putText(confirmation, "REGISTRATION COMPLETE", (70, 30), font, font_size, (0, 200, 0), 2)

            small_font_size = get_dynamic_font_size(400, 300, base_size=0.6, min_size=0.4, max_size=0.8)
            cv2.putText(confirmation, "Press any key to continue", (100, 280), font, small_font_size, (0, 0, 0), 1)

            # Create a named window with adjustable size
            cv2.namedWindow("Registration Complete", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Registration Complete", 400, 300)

            cv2.imshow("Registration Complete", confirmation)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

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


# Recognize a face using the webcam with anti-spoofing measures and improved UI
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
    micro_movements_verified = False
    in_blink = False
    blink_timestamps = []  # Store indices of detected blinks for visualization
    # For smoothing the EAR values
    ear_smoothing_window = 5
    recent_ears = []

    # Initialize variables for error reporting
    depth_variance = 0.0
    depth_range = 0.0
    verification_score = 0.0
    face = None

    # Add these initializations to avoid errors
    personal_threshold = 0.22  # Default value
    baseline_ear = 0.25  # Default value
    ear = 0.0  # Current EAR value
    pitch = 0.0  # Head pitch
    yaw = 0.0  # Head yaw
    movement_amount = 0.0  # Movement magnitude

    # Detection parameters with significantly increased sensitivity for research setting
    BLINK_CONSEC_FRAMES = 1  # Just 1 frame needed to count as blink starting
    BLINK_TOTAL_REQUIRED = 1  # Reduced to just 1 required blink for easier verification
    DEPTH_VARIANCE_THRESHOLD = 600.0  # Lowered threshold for easier depth verification
    DEPTH_RANGE_THRESHOLD = 25.0  # Lowered threshold for easier depth range verification
    MOVEMENT_THRESHOLD = 0.25  # Lowered for more sensitive movement detection
    MOVEMENT_FRAMES_REQUIRED = 6  # Fewer frames required for movement detection
    ROTATION_THRESHOLD = 3.0  # More sensitive rotation detection (3°)

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
    scores = {'blink': 0, 'depth': 0, 'dynamic': 0}

    # Open camera
    cap = cv2.VideoCapture(0)
    print("Looking for face... Please blink naturally and move your head slightly for verification.")

    # Create a named window with adjustable size
    cv2.namedWindow("Liveness Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Liveness Detection", 1280, 720)  # Widescreen format to fit panel

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

            # Get general lighting threshold with improved adaptivity
            EAR_THRESHOLD = get_adaptive_ear_threshold(frame, ear_values)

            # Detect face and landmarks
            try:
                face, eye_landmarks, face_box, depth_points, landmarks_3d = detect_face(frame)
            except Exception as e:
                print(f"Error in face detection: {str(e)}")

                # Create a simplified UI for face detection error
                display_frame = np.zeros((frame.shape[0], frame.shape[1] + 500, 3), dtype=np.uint8)
                display_frame[0:frame.shape[0], 0:frame.shape[1]] = frame
                cv2.putText(display_frame, "Face detection error", (10, 30), font, 0.7, (0, 0, 255), 2)

                cv2.imshow("Liveness Detection", display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            # Calculate remaining time
            elapsed_time = time.time() - start_time
            remaining_time = max(0, timeout - int(elapsed_time))

            # Check for timeout
            if remaining_time <= 0:
                print("Session timed out. Please try again.")
                break

            if face is not None and eye_landmarks is not None and depth_points is not None:
                left_eye, right_eye = eye_landmarks

                # Calculate EAR for both eyes
                left_ear = calculate_ear(left_eye)
                right_ear = calculate_ear(right_eye)

                # Average EAR
                current_ear = (left_ear + right_ear) / 2.0

                # Apply more aggressive smoothing to EAR values
                recent_ears.append(current_ear)
                if len(recent_ears) > ear_smoothing_window:
                    recent_ears.pop(0)

                # Apply weighted average with more weight to recent values
                if len(recent_ears) >= 3:
                    weights = np.linspace(0.5, 1.0, len(recent_ears))
                    weighted_sum = sum(w * e for w, e in zip(weights, recent_ears))
                    ear = weighted_sum / sum(weights)
                else:
                    ear = current_ear

                ear_values.append(ear)

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

                # Track blinks - completely redesigned blink detection for research setting
                if len(ear_values) > 5:
                    # Calculate baseline EAR for this person using a more stable method
                    # Use the upper quartile of values for baseline calculation
                    sorted_ear_values = sorted(ear_values[-30:] if len(ear_values) > 30 else ear_values)
                    upper_quartile_idx = int(len(sorted_ear_values) * 0.75)
                    baseline_ear = np.mean(sorted_ear_values[upper_quartile_idx:])

                    # Adaptive personal threshold based on observed variance
                    ear_std = np.std(ear_values[-20:]) if len(ear_values) > 20 else 0.02

                    # More sensitive threshold for research setting
                    # Higher baseline EARs (people with wider eyes) need a more sensitive multiplier
                    ear_multiplier = 0.92 if baseline_ear > 0.35 else 0.88

                    # Dynamic personal threshold based on baseline and variance
                    personal_threshold = baseline_ear * ear_multiplier

                    # For rapid detection, use recent history
                    window_size = min(10, len(ear_values))
                    recent_values = ear_values[-window_size:]
                    recent_min_ear = min(recent_values)
                    recent_max_ear = max(recent_values)

                    # Calculate downward velocity (rate of change)
                    if len(ear_values) >= 3:
                        ear_velocity = ear_values[-1] - ear_values[-3]
                    else:
                        ear_velocity = 0

                    # Multi-factor blink detection:
                    # 1. Current EAR below threshold
                    # 2. Significant recent change in EAR
                    # 3. Negative velocity (eye closing movement)
                    ear_change_ratio = (recent_max_ear - recent_min_ear) / (recent_max_ear + 1e-6)

                    blink_condition = (
                            ear < personal_threshold and
                            (ear_change_ratio > 0.05 or (recent_max_ear - ear) > 0.015) and
                            ear_velocity < -0.01 and
                            not in_blink
                    )

                    # Secondary detection for subtle blinks
                    subtle_blink_condition = (
                            not in_blink and
                            ear < (baseline_ear - 1.5 * ear_std) and
                            ear_velocity < -0.005
                    )

                    if blink_condition or subtle_blink_condition:
                        blink_frames += 1
                        if blink_frames >= BLINK_CONSEC_FRAMES:
                            in_blink = True
                            # Store timestamp (index) for visualization
                            blink_timestamps.append(len(ear_values) - 1)
                    elif in_blink and ear > (personal_threshold * 1.02):
                        in_blink = False
                        total_blinks += 1
                        blink_frames = 0

                # Check if we have enough blinks
                if total_blinks >= BLINK_TOTAL_REQUIRED:
                    blink_detected = True
                    scores['blink'] = 1.0  # Always give full score when required blinks detected
                elif total_blinks > 0:
                    # Partial credit for at least one blink
                    blink_detected = False
                    scores['blink'] = 0.7  # 70% credit for partial blinks

                # Calculate weighted verification score with blink prioritized
                verification_score = (
                        VALIDATION_WEIGHTS['blink'] * scores['blink'] +
                        VALIDATION_WEIGHTS['depth'] * scores['depth'] +
                        VALIDATION_WEIGHTS['dynamic'] * scores['dynamic']
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
                         dynamic_score * FUSION_WEIGHTS['dynamic'] >= 0.4) and  # Reduced from 0.5
                        verification_score >= 0.5  # Reduced from 0.6
                )

                # Create enhanced UI display with landmarks visualization and blink timestamps
                display_frame = integrate_improved_ui(
                    frame=frame,
                    ear_values=ear_values,
                    ear_threshold=EAR_THRESHOLD,
                    face_box=face_box,
                    eye_landmarks=eye_landmarks,
                    depth_verified=depth_verified,
                    depth_variance=depth_variance,
                    depth_range=depth_range,
                    movement_detected=movement_detected,
                    rotation_detected=rotation_detected,
                    movement_amount=movement_amount,
                    pitch=pitch,
                    yaw=yaw,
                    micro_movements_verified=micro_movements_verified,
                    blink_detected=blink_detected,
                    total_blinks=total_blinks,
                    blinks_required=BLINK_TOTAL_REQUIRED,
                    verification_score=verification_score,
                    final_verification=final_verification,
                    landmarks_3d=landmarks_3d,  # Pass landmarks for visualization
                    remaining_time=remaining_time,
                    personal_threshold=personal_threshold,
                    baseline_ear=baseline_ear,
                    ear=ear,
                    blink_timestamps=blink_timestamps  # Pass blink timestamps for visualization
                )

                if final_verification:
                    # Show verification message for a moment
                    cv2.imshow("Liveness Detection", display_frame)
                    cv2.waitKey(1000)
                    break
            else:
                # Create a simplified UI when no face is detected
                h, w = frame.shape[:2]
                panel_width = max(300, min(500, int(w * 0.5)))  # Dynamic panel width
                display_frame = np.zeros((h, w + panel_width, 3), dtype=np.uint8)
                display_frame[0:h, 0:w] = frame

                # Fill right panel
                panel_x = w
                display_frame[:, panel_x:panel_x + panel_width] = [240, 240, 240]  # Light gray

                # Add title bar with dynamic sizing
                title_height = int(h * 0.07)
                cv2.rectangle(display_frame, (panel_x, 0), (panel_x + panel_width, title_height), (70, 70, 70), -1)

                # Get dynamic font sizes
                title_font_size = get_dynamic_font_size(w, h, base_size=0.8, min_size=0.6, max_size=1.0)
                msg_font_size = get_dynamic_font_size(w, h, base_size=1.0, min_size=0.7, max_size=1.2)
                small_font_size = get_dynamic_font_size(w, h, base_size=0.7, min_size=0.5, max_size=0.9)

                cv2.putText(display_frame, "LIVENESS DETECTION SYSTEM",
                            (panel_x + 10, title_height - 15),
                            font, title_font_size, (240, 240, 240), 2)

                # Add no face detected message
                cv2.putText(display_frame, "No face detected",
                            (panel_x + panel_width // 4, h // 3),
                            font, msg_font_size, (0, 0, 200), 2)
                cv2.putText(display_frame, "Please position your face in the frame",
                            (panel_x + panel_width // 8, h // 3 + 50),
                            font, small_font_size, (0, 0, 0), 1)

                # Show timer
                cv2.putText(display_frame, f"Time Remaining: {remaining_time}s",
                            (panel_x + panel_width // 4, h - 50), font, small_font_size, (0, 0, 0), 1)

                scores = {'blink': 0, 'depth': 0, 'dynamic': 0}

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
                    VALIDATION_WEIGHTS['dynamic'] * scores['dynamic']
            )

            # Modified verification logic with higher priority for blink
            static_score = depth_verified
            dynamic_score = movement_detected or rotation_detected or micro_movements_verified

            # Final verification requires adjusted logic
            liveness_verified = (
                    (blink_detected or total_blinks >= 1) and  # Even 1 blink is acceptable
                    (static_score * FUSION_WEIGHTS['static'] +
                     dynamic_score * FUSION_WEIGHTS['dynamic'] >= 0.4) and  # Reduced from 0.5
                    verification_score >= 0.5  # Reduced from 0.6
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

            print(f"- Overall verification score: {verification_score:.2f}/0.5 required")
            return False

        print("Liveness verified! Proceeding with face recognition...")

        # Now proceed with face recognition since liveness is verified
        if face is not None:
            try:
                test_features = extract_features(face)
                similarity = 1 - cosine(registered_features, test_features)

                # Create result screen with dynamic sizing
                h, w = face.shape[:2]
                result_width = 800
                result_height = 400
                result_screen = np.zeros((result_height, result_width, 3), dtype=np.uint8)
                result_screen[:] = (240, 240, 240)  # Light gray background

                # Add title
                cv2.rectangle(result_screen, (0, 0), (result_width, 60), (70, 70, 70), -1)

                # Calculate dynamic font sizes
                title_font_size = get_dynamic_font_size(result_width, result_height, base_size=1.2, min_size=0.8,
                                                        max_size=1.5)
                section_font_size = get_dynamic_font_size(result_width, result_height, base_size=0.8, min_size=0.6,
                                                          max_size=1.0)
                item_font_size = get_dynamic_font_size(result_width, result_height, base_size=0.6, min_size=0.4,
                                                       max_size=0.8)

                cv2.putText(result_screen, "FACE RECOGNITION RESULTS",
                            (int(result_width * 0.2), 40),
                            font, title_font_size, (255, 255, 255), 2)

                # Display the face
                if face.shape[0] > 0 and face.shape[1] > 0:
                    face_resized = cv2.resize(face, (200, 200))
                    result_screen[100:300, 50:250] = face_resized

                # Show verification results
                y_pos = 120
                cv2.putText(result_screen, "VERIFICATION RESULTS:", (300, y_pos),
                            font, section_font_size, (0, 0, 0), 1)
                y_pos += 40

                # Show individual verification items
                items = [
                    f"Blink Detection: {total_blinks}/{BLINK_TOTAL_REQUIRED}",
                    f"Depth Verification: {'Passed' if depth_verified else 'Failed'}",
                    f"Movement Detection: {'Passed' if movement_detected else 'Failed'}",
                    f"Rotation Detection: {'Passed' if rotation_detected else 'Failed'}",
                    f"Micro-movements: {'Natural' if micro_movements_verified else 'Unnatural'}"
                ]

                for item in items:
                    cv2.putText(result_screen, item, (300, y_pos),
                                font, item_font_size, (0, 0, 0), 1)
                    y_pos += 30

                # Show recognition results
                y_pos += 20
                cv2.putText(result_screen, f"RECOGNITION SIMILARITY: {similarity:.2f}",
                            (300, y_pos), font, section_font_size, (0, 0, 0), 1)

                # Final result
                is_recognized = similarity > 0.60
                y_pos += 50

                if is_recognized:
                    cv2.rectangle(result_screen, (250, y_pos - 40), (700, y_pos + 10), (0, 200, 0), -1)
                    cv2.putText(result_screen, "FACE RECOGNIZED", (320, y_pos),
                                font, section_font_size, (255, 255, 255), 2)
                else:
                    cv2.rectangle(result_screen, (250, y_pos - 40), (700, y_pos + 10), (0, 0, 200), -1)
                    cv2.putText(result_screen, "FACE NOT RECOGNIZED", (300, y_pos),
                                font, section_font_size, (255, 255, 255), 2)

                # Create a named window with adjustable size
                cv2.namedWindow("Recognition Results", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Recognition Results", result_width, result_height)

                # Display result
                cv2.imshow("Recognition Results", result_screen)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

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