import cv2
import numpy as np
import mediapipe as mp
from sklearn.preprocessing import normalize
from scipy.spatial.distance import cosine
import os
import time
from datetime import datetime

class LightweightFRS:
    def __init__(self):
        # Initialize MediaPipe solutions with image dimensions
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            refine_landmarks=False
        )

        # Initialize face detector
        self.face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        # Constants
        self.DESIRED_FACE_WIDTH = 160
        self.DESIRED_FACE_HEIGHT = 160
        self.DESIRED_FACE_AREA = (self.DESIRED_FACE_WIDTH * self.DESIRED_FACE_HEIGHT)
        self.FACE_AREA_TOLERANCE = 0.2

        # Eye blink detection parameters
        self.EYE_AR_THRESH = 0.2
        self.EYE_AR_CONSEC_FRAMES = 2
        self.COUNTER = 0
        self.TOTAL_BLINKS = 0

        # Create directory for captured images
        self.capture_dir = "../../../ML/captured_faces"
        if not os.path.exists(self.capture_dir):
            os.makedirs(self.capture_dir)

    def get_face_position_guidance(self, face_bbox, frame_shape):
        """Provide guidance for face positioning"""
        frame_h, frame_w = frame_shape[:2]
        x, y, w, h = face_bbox

        # Calculate relative position
        face_center_x = x + w / 2
        face_center_y = y + h / 2
        rel_x = face_center_x / frame_w
        rel_y = face_center_y / frame_h

        messages = []

        # Distance check
        face_area = w * h
        face_area_ratio = face_area / (frame_w * frame_h)

        if face_area_ratio < 0.15:
            messages.append("Move closer")
        elif face_area_ratio > 0.65:
            messages.append("Move back")

        # Position check
        if rel_x < 0.4:
            messages.append("Move right")
        elif rel_x > 0.6:
            messages.append("Move left")

        if rel_y < 0.4:
            messages.append("Move down")
        elif rel_y > 0.6:
            messages.append("Move up")

        return messages

    def calculate_eye_aspect_ratio(self, eye_landmarks):
        """Calculate the eye aspect ratio"""
        height_1 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        height_2 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        width = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])

        ear = (height_1 + height_2) / (2.0 * width) if width > 0 else 0
        return ear

    def detect_blink(self, frame):
        """Detect eye blinks"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape
        results = self.face_mesh.process(frame_rgb)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            # Extract eye landmarks
            left_eye = np.array([[landmarks[p].x * w, landmarks[p].y * h]
                                 for p in [33, 160, 158, 133, 153, 144]])

            right_eye = np.array([[landmarks[p].x * w, landmarks[p].y * h]
                                  for p in [362, 385, 387, 263, 373, 380]])

            # Calculate EAR
            left_ear = self.calculate_eye_aspect_ratio(left_eye)
            right_ear = self.calculate_eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0

            if ear < self.EYE_AR_THRESH:
                self.COUNTER += 1
            else:
                if self.COUNTER >= self.EYE_AR_CONSEC_FRAMES:
                    self.TOTAL_BLINKS += 1
                self.COUNTER = 0

            return self.TOTAL_BLINKS > 0
        return False

    def extract_face_features(self, face_img):
        """Extract face features using HOG"""
        # Resize for consistency
        face_img = cv2.resize(face_img, (self.DESIRED_FACE_WIDTH, self.DESIRED_FACE_HEIGHT))
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)

        # Calculate HOG features
        win_size = (160, 160)
        block_size = (16, 16)
        block_stride = (8, 8)
        cell_size = (8, 8)
        nbins = 9

        hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
        features = hog.compute(gray)

        # Normalize features
        normalized_features = normalize(features.reshape(1, -1))
        return normalized_features.flatten()

    def check_spoof(self, frame):
        """Check for spoofing attempts"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Check for blur (printed photos tend to have less texture)
        if blur < 100:  # Threshold for blur detection
            return False

        # Check for face depth using face mesh
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            depths = [landmark.z for landmark in landmarks]
            depth_variance = np.std(depths)

            if depth_variance < 0.01:  # Threshold for depth variance
                return False

        return True

    def register_face(self):
        """Register a face"""
        print("Registration started. Please position your face and blink naturally...")
        cap = cv2.VideoCapture(0)
        start_time = time.time()
        timeout = 30

        while (time.time() - start_time) < timeout:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect face
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

            if len(faces) > 0:
                x, y, w, h = faces[0]
                # Get position guidance
                guidance = self.get_face_position_guidance((x, y, w, h), frame.shape)

                # Draw face rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Display guidance
                for i, message in enumerate(guidance):
                    cv2.putText(frame, message, (10, 30 + i * 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                if not guidance:  # Face is well-positioned
                    if not self.check_spoof(frame):
                        cv2.putText(frame, "Spoof detected!", (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        continue

                    blink_detected = self.detect_blink(frame)
                    cv2.putText(frame, f"Blinks: {self.TOTAL_BLINKS}", (10, 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                    if blink_detected:
                        face_img = frame[y:y + h, x:x + w]
                        features = self.extract_face_features(face_img)

                        # Save face image
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        img_path = os.path.join(self.capture_dir, f"face_{timestamp}.jpg")
                        cv2.imwrite(img_path, face_img)

                        cap.release()
                        cv2.destroyAllWindows()
                        print("Registration successful!")
                        return features

            cv2.imshow("Registration", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        print("Registration failed or timed out!")
        return None

    def recognize_face(self, registered_features):
        """Recognize a face"""
        print("Recognition started. Please position your face and blink...")
        cap = cv2.VideoCapture(0)
        start_time = time.time()
        timeout = 30

        while (time.time() - start_time) < timeout:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

            if len(faces) > 0:
                x, y, w, h = faces[0]
                guidance = self.get_face_position_guidance((x, y, w, h), frame.shape)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                for i, message in enumerate(guidance):
                    cv2.putText(frame, message, (10, 30 + i * 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                if not guidance:  # Face is well-positioned
                    if not self.check_spoof(frame):
                        cv2.putText(frame, "Spoof detected!", (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        continue

                    blink_detected = self.detect_blink(frame)
                    cv2.putText(frame, f"Blinks: {self.TOTAL_BLINKS}", (10, 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                    if blink_detected:
                        face_img = frame[y:y + h, x:x + w]
                        test_features = self.extract_face_features(face_img)
                        similarity = 1 - cosine(registered_features, test_features)

                        cap.release()
                        cv2.destroyAllWindows()

                        if similarity > 0.65:
                            print(f"Face recognized! Similarity: {similarity:.2f}")
                            return True
                        else:
                            print(f"Face not recognized. Similarity: {similarity:.2f}")
                            return False

            cv2.imshow("Recognition", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        print("Recognition failed or timed out!")
        return False


def main():
    print("Initializing Face Recognition System...")
    frs = LightweightFRS()

    print("\nStarting face registration...")
    registered_features = frs.register_face()

    if registered_features is not None:
        print("\nStarting face recognition...")
        if frs.recognize_face(registered_features):
            print("Authentication successful!")
        else:
            print("Authentication failed!")
    else:
        print("Registration failed. Please try again.")


if __name__ == "__main__":
    main()