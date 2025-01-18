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
        });
    });

    // Add event listener to the close button
    closeButton.addEventListener('click', () => {
        fadeOut(infoContent3, function () {
            infoContent3.style.display = 'none'; // Hide info-content-3
            infoContent1.style.display = 'block'; // Show info-content-1
            fadeIn(infoContent1); // Fade in info-content-1
        });
    });

    // Function to start the camera
    async function startCamera() {
        const video = document.getElementById('video');
        const scannerIcon = document.querySelector('.scanner-icon');

        try {
            // Request access to the user's camera
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            // Set the video source to the camera stream
            video.srcObject = stream;
            // Show the video element and hide the scanner icon
            video.style.display = 'block';
            scannerIcon.style.display = 'none';
        } catch (error) {
            console.error("Error accessing the camera: ", error);
        }
    }

    // Add event listener to the scan button
    document.querySelector('.scan-button-main').addEventListener('click', startCamera);

    // Start the camera when the page loads (optional, can be removed if you want to start only on button click)
    window.onload = function () {
        const video = document.getElementById('video');
        video.style.display = 'none'; // Hide video initially
    };

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
});