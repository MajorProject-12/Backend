import os
import cv2
import numpy as np
import time
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.applications import MobileNetV3Large
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import img_to_array, ImageDataGenerator
import threading
from django.conf import settings
from authentication.models import Student

# Define paths for the facial recognition system
FACE_DATASET_DIR = os.path.join(settings.MEDIA_ROOT, 'face_dataset')
TRAIN_DIR = os.path.join(FACE_DATASET_DIR, 'train')
TEST_DIR = os.path.join(FACE_DATASET_DIR, 'test')
MODEL_PATH = os.path.join(FACE_DATASET_DIR, 'face_recognition_model.keras')


# Make sure directories exist
def ensure_dirs_exist():
    """Ensure all required directories exist"""
    os.makedirs(FACE_DATASET_DIR, exist_ok=True)
    os.makedirs(TRAIN_DIR, exist_ok=True)
    os.makedirs(TEST_DIR, exist_ok=True)

    # Create a placeholder to initialize model if it doesn't exist
    if not os.path.exists(MODEL_PATH):
        initialize_model()


def initialize_model():
    """Initialize a new model if one doesn't exist"""
    print("Initializing new face recognition model...")
    base_model = MobileNetV3Large(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    x = GlobalAveragePooling2D(name="global_avg_pooling_new")(base_model.output)
    x = Dropout(0.3, name="dropout_new")(x)
    x = Dense(128, activation='relu', name="dense_new_1")(x)
    x = Dropout(0.3, name="dropout_new_2")(x)

    # Default to 1 class (will be updated when users register)
    output = Dense(1, activation='softmax', name="output_new_layer")(x)
    model = Model(inputs=base_model.input, outputs=output)

    model.compile(optimizer=Adam(learning_rate=0.0001),
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    model.save(MODEL_PATH)
    print("✅ Initial model created successfully!")


def is_live_face(frame, gray, x, y, w, h):
    """Detects if a real face with eyes is present (for liveliness detection)"""
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    face_roi = gray[y:y + h, x:x + w]
    eyes = eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
    return len(eyes) > 0  # Return True if eyes are detected (not a static image)


def detect_face(frame):
    """Detect face in a frame and return the face area"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(100, 100))

    if len(faces) == 0:
        return None

    # Get the largest face in the frame
    largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
    x, y, w, h = largest_face

    # Check if face is live
    if not is_live_face(frame, gray, x, y, w, h):
        return None

    # Get the face area
    face_area = frame[y:y + h, x:x + w]
    return face_area


def face_already_exists(face):
    """Check if a face already exists under a different name in the dataset"""
    try:
        model = load_model(MODEL_PATH)
        face = cv2.resize(face, (224, 224))
        face = img_to_array(face)
        face = np.expand_dims(face, axis=0)

        predictions = model.predict(face)
        confidence = np.max(predictions)

        if confidence > 0.7:  # If face matches an existing user
            return True
        return False
    except Exception as e:
        print(f"Error in face_already_exists: {e}")
        return False


def register_user_face(student, frame):
    """Register a student's face, capturing from provided frame"""
    try:
        # Ensure directories exist
        ensure_dirs_exist()

        # Create user directories
        username = student.roll_number
        user_train_path = os.path.join(TRAIN_DIR, username)
        user_test_path = os.path.join(TEST_DIR, username)

        os.makedirs(user_train_path, exist_ok=True)
        os.makedirs(user_test_path, exist_ok=True)

        # Detect face in the frame
        face_area = detect_face(frame)
        if face_area is None:
            return False, "No face detected or face not live. Please ensure your face is visible and try again."

        # Check if face already exists
        if face_already_exists(face_area):
            return False, "Face already registered under a different username. Registration denied."

        # Save multiple variants of the face image for better training
        # This simulates capturing multiple frames from webcam
        for count in range(30):
            # Create slight variations in the image to simulate different frames
            if count > 0:
                # Apply small random transformations
                angle = np.random.uniform(-10, 10)
                scale = np.random.uniform(0.95, 1.05)
                rows, cols = face_area.shape[:2]
                M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, scale)
                face_variant = cv2.warpAffine(face_area, M, (cols, rows))
            else:
                face_variant = face_area.copy()

            # Resize for model input
            face_resized = cv2.resize(face_variant, (224, 224))

            # Save to appropriate directory (first 20 for training, last 10 for testing)
            save_path = user_train_path if count < 20 else user_test_path
            cv2.imwrite(os.path.join(save_path, f"{username}_{count}.jpg"), face_resized)

        # Train model with the new user data
        train_success = train_single_user(username)
        if train_success:
            return True, "Face registered successfully and model updated."
        else:
            return False, "Face registered but model training failed."

    except Exception as e:
        print(f"Error in register_user_face: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Registration error: {str(e)}"


def train_single_user(username):
    """Train the model with a single new user's images"""
    try:
        model = load_model(MODEL_PATH)

        # Get all registered users (including the new one)
        all_users = [d for d in os.listdir(TRAIN_DIR) if os.path.isdir(os.path.join(TRAIN_DIR, d))]
        num_classes = len(all_users)

        # If no users, return
        if num_classes == 0:
            print("No users to train")
            return False

        # Set up data generator
        data_gen = ImageDataGenerator(
            rescale=1. / 255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            horizontal_flip=True,
            brightness_range=[0.8, 1.2]
        )

        train_generator = data_gen.flow_from_directory(
            TRAIN_DIR,
            target_size=(224, 224),
            batch_size=8,
            class_mode='categorical'
        )

        # Check if model output layer needs to be updated
        if model.output_shape[-1] != num_classes:
            # Create new model with correct output size
            x = model.layers[-3].output  # Get pre-final layer
            new_output = Dense(num_classes, activation='softmax', name="new_output_layer")(x)
            model = Model(inputs=model.input, outputs=new_output)

        # Freeze early layers for transfer learning
        for layer in model.layers[:-4]:
            layer.trainable = False

        model.compile(optimizer=Adam(learning_rate=0.0001),
                      loss='categorical_crossentropy',
                      metrics=['accuracy'])

        # Train the model
        model.fit(train_generator, epochs=3, verbose=1)
        model.save(MODEL_PATH)
        print(f"✅ Model trained successfully for user {username}!")
        return True

    except Exception as e:
        print(f"Error in train_single_user: {e}")
        import traceback
        traceback.print_exc()
        return False


def recognize_user(frame):
    """Recognize a user from a frame"""
    try:
        # Detect face in the frame
        face_area = detect_face(frame)
        if face_area is None:
            return None, "No face detected or face not live"

        # Load model and class names
        model = load_model(MODEL_PATH)
        class_names = sorted(os.listdir(TRAIN_DIR))

        # Process face for recognition
        face_resized = cv2.resize(face_area, (224, 224))
        face = img_to_array(face_resized)
        face = np.expand_dims(face, axis=0)

        # Make prediction
        predictions = model.predict(face)
        label = np.argmax(predictions)
        confidence = np.max(predictions)

        if confidence > 0.7 and label < len(class_names):
            username = class_names[label]
            return username, confidence
        else:
            return None, "Unknown face"

    except Exception as e:
        print(f"Error in recognize_user: {e}")
        return None, str(e)


# Initialize the system when this module is imported
ensure_dirs_exist()