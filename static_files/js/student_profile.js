document.addEventListener("DOMContentLoaded", function () {
    // Get references to the elements
    const editButton = document.querySelector('.edit-button');
    const backIcon = document.querySelector('.back-icon');
    const infoContent1 = document.querySelector('.info-content-1');
    const infoContent2 = document.querySelector('.info-content-2');
    const infoContent3 = document.querySelector('.info-content-3');
    const saveButton = document.getElementById('save-button');
    const editProfileForm = document.getElementById('editProfileForm');
    const closeButton = document.querySelector('.close-button');
    const videoElement = document.getElementById('webcam');
    const captureButton = document.getElementById('capture-btn');
    const registrationStatus = document.getElementById('registration-status');
    const faceStatus = document.getElementById('face-status');
    const faceGuide = document.querySelector('.face-guide');
    const scannerIcon = document.querySelector('.scanner-icon');
    const canvas = document.createElement('canvas'); // Hidden canvas for capturing frames

    // Add event listener to the Edit button
    editButton.addEventListener('click', () => {
        fadeOut(infoContent1, function () {
            infoContent1.style.display = 'none'; // Hide info-content-1
            infoContent2.style.display = 'block'; // Show info-content-2
            fadeIn(infoContent2); // Fade in info-content-2
        });
    });

    // Add event listener to the Back icon
    backIcon.addEventListener('click', () => {
        fadeOut(infoContent2, function () {
            infoContent2.style.display = 'none'; // Hide info-content-2
            infoContent1.style.display = 'block'; // Show info-content-1
            fadeIn(infoContent1); // Fade in info-content-1
            editProfileForm.reset(); // Reset the form fields
        });
    });

    // Add event listener to the Save button
    saveButton.addEventListener('click', function() {
        editProfileForm.submit(); // Save changes
    });

    // Add event listener to the scan button
    document.querySelector('.scan-button').addEventListener('click', () => {
        fadeOut(infoContent1, function () {
            infoContent1.style.display = 'none'; // Hide info-content-1
            infoContent3.style.display = 'block'; // Show info-content-3
            fadeIn(infoContent3); // Fade in info-content-3
            // Initialize webcam when face scanner is opened
            initWebcam();
        });
    });

    // Add event listener to the close button
    closeButton.addEventListener('click', () => {
        fadeOut(infoContent3, function () {
            infoContent3.style.display = 'none'; // Hide info-content-3
            infoContent1.style.display = 'block'; // Show info-content-1
            fadeIn(infoContent1); // Fade in info-content-1
            // Stop webcam stream when closing the face scanner
            stopWebcam();
        });
    });

    // Check if browser supports mediaDevices API
    function checkWebcamSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            registrationStatus.textContent = 'Error: Your browser does not support webcam access.';
            console.error('mediaDevices API or getUserMedia not supported');
            return false;
        }
        return true;
    }

    // Get access to webcam with better error handling
    async function initWebcam() {
        registrationStatus.textContent = 'Initializing webcam...';
        console.log('Attempting to initialize webcam...');

        // First check if browser supports the required APIs
        if (!checkWebcamSupport()) {
            return;
        }

        try {
            console.log('Requesting webcam access...');
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            };

            console.log('Constraints:', constraints);
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            console.log('Webcam stream obtained successfully');

            // Check if video element exists
            if (!videoElement) {
                console.error('Video element not found!');
                registrationStatus.textContent = 'Error: Video element not found on page.';
                return;
            }

            videoElement.srcObject = stream;
            console.log('Stream attached to video element');

            // Enable capture button once webcam is ready
            videoElement.onloadedmetadata = () => {
                console.log('Video metadata loaded');
                captureButton.disabled = false;
                registrationStatus.textContent = 'Webcam ready. Position your face and click "Capture"';
                videoElement.style.display = 'block';
                scannerIcon.style.display = 'none';
                faceGuide.style.display = 'block';
            };

            // Add error handler for video element
            videoElement.onerror = (error) => {
                console.error('Video element error:', error);
                registrationStatus.textContent = `Video error: ${error.message}`;
            };
        } catch (error) {
            console.error('Error accessing webcam:', error);

            // Create more user-friendly error messages
            let errorMessage = '';
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                errorMessage = 'Camera access denied. Please allow camera access and try again.';
            } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                errorMessage = 'No camera found. Please connect a camera and try again.';
            } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                errorMessage = 'Camera is in use by another application. Please close other apps using the camera.';
            } else if (error.name === 'OverconstrainedError') {
                errorMessage = 'Camera does not meet the required constraints.';
            } else if (error.name === 'TypeError') {
                errorMessage = 'Invalid constraints specified.';
            } else {
                errorMessage = `Webcam error: ${error.message}`;
            }

            registrationStatus.textContent = errorMessage;
            // Make capture button unavailable and show error UI state
            if (captureButton) captureButton.disabled = true;
        }
    }

    // Stop webcam stream
    function stopWebcam() {
        console.log('Stopping webcam...');
        if (videoElement && videoElement.srcObject) {
            const tracks = videoElement.srcObject.getTracks();
            tracks.forEach(track => {
                console.log('Stopping track:', track.kind);
                track.stop();
            });
            videoElement.srcObject = null;
            videoElement.style.display = 'none';
            scannerIcon.style.display = 'block';
            faceGuide.style.display = 'none';
            console.log('Webcam stopped successfully');
        } else {
            console.log('No webcam stream to stop');
        }
    }

    // Capture image from webcam
    function captureImage() {
        console.log('Capturing image from webcam...');
        if (!videoElement || !videoElement.srcObject || videoElement.videoWidth === 0) {
            registrationStatus.textContent = 'Error: Webcam not ready. Please reload the page and try again.';
            console.error('Video element not ready for capture');
            return;
        }

        // Set canvas dimensions to match video
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        console.log(`Canvas dimensions set to ${canvas.width}x${canvas.height}`);

        // Draw current video frame to canvas
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

        // Convert canvas to base64 image data
        const imageData = canvas.toDataURL('image/jpeg', 0.9); // 90% quality JPEG

        // Log the size for debugging
        console.log(`Captured image data length: ${imageData.length}`);

        // Send to server if we have valid data
        if (imageData.length > 100) { // Basic validation
            registrationStatus.textContent = 'Processing image...';
            sendImageToServer(imageData);
        } else {
            registrationStatus.textContent = 'Error: Failed to capture valid image.';
            console.error('Invalid image data captured');
        }
    }

    // Send image to Django backend
    async function sendImageToServer(imageData) {
        console.log('Sending image to server...');
        try {
            registrationStatus.textContent = 'Sending to server...';

            const csrfToken = getCSRFToken();
            console.log('CSRF token obtained:', csrfToken ? 'Yes' : 'No');

            const response = await fetch('/api/process-registration/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken // Get CSRF token from cookie
                },
                body: JSON.stringify({
                    image: imageData
                })
            });

            console.log('Server response received:', response.status);

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('Response data:', result);

            // Display result
            registrationStatus.textContent = result.message;

            // Update face status in main view
            if (result.completed) {
                faceStatus.textContent = 'Registered';
                console.log('Face registration successful!');

                // Return to main profile view after successful registration
                setTimeout(() => {
                    fadeOut(infoContent3, function () {
                        infoContent3.style.display = 'none';
                        infoContent1.style.display = 'block';
                        fadeIn(infoContent1);
                        stopWebcam();
                    });
                }, 2000);
            }

        } catch (error) {
            console.error('Error sending image:', error);
            registrationStatus.textContent = `Error: ${error.message}`;
        }
    }

    // Get CSRF token from cookies
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue;
    }

    // Add event listener to the capture button
    if (captureButton) {
        captureButton.addEventListener('click', captureImage);
        console.log('Capture button listener added');
    } else {
        console.error('Capture button not found!');
    }

    // Function to fade out an element
    function fadeOut(element, callback) {
        let opacity = 1;
        const interval = setInterval(function () {
            if (opacity > 0) {
                opacity -= 0.3;
                element.style.opacity = opacity;
            } else {
                clearInterval(interval);
                if (callback) callback();
            }
        }, 50);
    }

    // Function to fade in an element
    function fadeIn(element) {
        let opacity = 0;
        element.style.opacity = opacity;
        element.style.display = 'block'; // Ensure the element is visible
        const interval = setInterval(function () {
            if (opacity < 1) {
                opacity += 0.3;
                element.style.opacity = opacity;
            } else {
                clearInterval(interval);
            }
        }, 50);
    }

    // Check elements on load
    console.log('DOM loaded, checking elements:');
    console.log('Video element exists:', !!videoElement);
    console.log('Capture button exists:', !!captureButton);
    console.log('Registration status exists:', !!registrationStatus);
});