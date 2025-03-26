import cv2
import os
import time


def capture_faces(save_dir='captured_faces', max_images=50):
    # Load Haar cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Create directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Start video capture
    cap = cv2.VideoCapture(0)

    count = 0
    while count < max_images:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        for (x, y, w, h) in faces:
            face = frame[y:y + h, x:x + w]
            face_filename = os.path.join(save_dir, f'face_{count + 1}.jpg')
            cv2.imwrite(face_filename, face)
            count += 1

            # Draw rectangle around detected face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if count >= max_images:
                break

        cv2.imshow('Face Capture', frame)
        time.sleep(2)  # Wait for 2 seconds before capturing next frame

        # Press 'q' to exit early
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Captured {count} face images in '{save_dir}'")


if __name__ == '__main__':
    capture_faces()
