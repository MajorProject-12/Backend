document.addEventListener("DOMContentLoaded", function () {
    // Existing elements from the profile page
    const editButton = document.querySelector('.edit-button');
    const backIcon = document.querySelector('.back-icon');
    const infoContent1 = document.querySelector('.info-content-1');
    const infoContent2 = document.querySelector('.info-content-2');
    const infoContent3 = document.querySelector('.info-content-3');
    const saveButton = document.getElementById('save-button');
    const editProfileForm = document.getElementById('editProfileForm');
    const closeButton = document.querySelector('.close-button');

    // New elements for face recognition
    const scanButton = document.querySelector('.scan-button');
    const scanButtonMain = document.querySelector('.scan-button-main');
    const video = document.getElementById('video'); // video element inside info-content-3 (scanner)
    const messageDiv = document.getElementById('message');

    // --- Fade in/out functions ---
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

    function fadeIn(element) {
        let opacity = 0;
        element.style.opacity = opacity;
        element.style.display = 'block';
        const interval = setInterval(function () {
            if (opacity < 1) {
                opacity += 0.3;
                element.style.opacity = opacity;
            } else {
                clearInterval(interval);
            }
        }, 50);
    }

    // --- Existing event listeners for editing profile ---
    editButton.addEventListener('click', () => {
        fadeOut(infoContent1, function () {
            infoContent1.style.display = 'none';
            infoContent2.style.display = 'block';
            fadeIn(infoContent2);
        });
    });

    backIcon.addEventListener('click', () => {
        fadeOut(infoContent2, function () {
            infoContent2.style.display = 'none';
            infoContent1.style.display = 'block';
            fadeIn(infoContent1);
            editProfileForm.reset();
        });
    });

    saveButton.addEventListener('click', function() {
        editProfileForm.submit();
    });

    // Show the scanner when the scan button is clicked
    scanButton.addEventListener('click', () => {
        fadeOut(infoContent1, function () {
            infoContent1.style.display = 'none';
            infoContent3.style.display = 'block';
            fadeIn(infoContent3);
            startCamera(); // start the webcam in the scanner view
        });
    });

    closeButton.addEventListener('click', () => {
        fadeOut(infoContent3, function () {
            infoContent3.style.display = 'none';
            infoContent1.style.display = 'block';
            fadeIn(infoContent1);
        });
    });

    // --- Face Recognition / Registration functionality ---

    // Start the webcam on scanner view and wait until video dimensions are ready
    async function startCamera() {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                video.srcObject = stream;
                // Wait for metadata to load
                await new Promise(resolve => {
                    video.onloadedmetadata = () => {
                        console.log("Video metadata loaded:", video.videoWidth, video.videoHeight);
                        resolve();
                    };
                });
                // Additional wait until dimensions are nonzero (up to 1 second)
                let attempts = 0;
                while (video.videoWidth === 0 && attempts < 10) {
                    await new Promise(r => setTimeout(r, 100));
                    attempts++;
                }
                if (video.videoWidth === 0) {
                    displayMessage("Video not ready. Please try again.");
                } else {
                    video.style.display = 'block';
                    console.log("Video dimensions ready:", video.videoWidth, video.videoHeight);
                }
            } catch (error) {
                console.error("Error accessing webcam: ", error);
                displayMessage("Error accessing webcam.");
            }
        } else {
            displayMessage("Webcam not supported in this browser.");
        }
    }

    // Capture image from the video element
    function captureImage() {
        if (video.videoWidth === 0 || video.videoHeight === 0) {
            displayMessage("Camera not ready. Please wait a moment and try again.");
            return null;
        }
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0);
        const imageData = canvas.toDataURL('image/jpeg');
        console.log("Captured image data length:", imageData.length);
        return imageData;
    }

    // Main event listener for the scan button that triggers registration or attendance
    scanButtonMain.addEventListener('click', async () => {
        // Ensure the camera is started and ready
        await startCamera();
        // Delay capture to allow the stream to stabilize
        setTimeout(() => {
            const imageData = captureImage();
            if (!imageData) return; // Stop if capture fails

            // Check registration status before proceeding
            fetch('/check_registration/')
                .then(response => response.json())
                .then(data => {
                    if (data.is_registered) {
                        markAttendance(imageData);
                    } else {
                        registerFace(imageData);
                    }
                })
                .catch(error => {
                    console.error("Error checking registration status: ", error);
                    displayMessage("Error checking registration status.");
                });
        }, 500);
    });

    // Check registration status and update UI label accordingly
    function checkRegistrationStatus() {
        fetch('/check_registration/')
            .then(response => response.json())
            .then(data => {
                const faceStatusSpan = document.querySelector('.face-recognition-section span');
                if (data.is_registered) {
                    faceStatusSpan.textContent = "Face Recognition: Registered";
                } else {
                    faceStatusSpan.textContent = "Face Recognition: Unregistered";
                }
            })
            .catch(error => {
                console.error("Error checking registration: ", error);
            });
    }

    // Send captured image to register face endpoint
    function registerFace(imageData) {
        fetch('/register_face/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => response.json())
        .then(data => {
            displayMessage(data.message);
            if (data.message === "Face registered successfully") {
                const faceStatusSpan = document.querySelector('.face-recognition-section span');
                faceStatusSpan.textContent = "Face Recognition: Registered";
            }
        })
        .catch(error => {
            console.error("Error during registration: ", error);
            displayMessage("An error occurred while registering the face.");
        });
    }

    // Send captured image to mark attendance endpoint
    function markAttendance(imageData) {
        fetch('/mark_attendance/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => response.json())
        .then(data => {
            displayMessage(data.message);
        })
        .catch(error => {
            console.error("Error during marking attendance: ", error);
            displayMessage("An error occurred while marking attendance.");
        });
    }

    // Utility to display messages
    function displayMessage(msg) {
        messageDiv.textContent = msg;
        messageDiv.classList.remove("d-none");
    }

    // Utility to get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // On page load, check registration status
    checkRegistrationStatus();
});
