document.addEventListener('DOMContentLoaded', () => {
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
            document.querySelector('.scan-button').addEventListener('click', startCamera);
    
            // Start the camera when the page loads (optional, can be removed if you want to start only on button click)
            window.onload = function () {
                const video = document.getElementById('video');
                video.style.display = 'none'; // Hide video initially
            };
});