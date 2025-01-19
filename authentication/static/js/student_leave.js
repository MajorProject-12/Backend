// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
    // Get references to the buttons and containers
    const newButton = document.querySelector(".new");
    const recordsButton = document.querySelector(".records");
    const container1 = document.querySelector(".container-1");
    const container2 = document.querySelector(".container-2");

    // Add event listeners to the buttons
    newButton.addEventListener("click", function () {
        // Only proceed if container-1 is not already displayed
        if (container1.style.display !== "block") {
            // Fade in container-1 and hide container-2
            container1.style.display = "block";
            container1.style.opacity = 0;
            fadeIn(container1);

            container2.style.display = "none";
        }
    });

    recordsButton.addEventListener("click", function () {
        // Only proceed if container-2 is not already displayed
        if (container2.style.display !== "block") {
            // Fade in container-2 and hide container-1
            container2.style.display = "block";
            container2.style.opacity = 0;
            fadeIn(container2);

            container1.style.display = "none";
        }
    });

    // Function to fade in an element
    function fadeIn(element) {
        let opacity = 0;
        const interval = setInterval(function () {
            if (opacity < 1) {
                opacity += 0.2;
                element.style.opacity = opacity;
            } else {
                clearInterval(interval);
            }
        }, 50);
    }

    // Function to set status background colors based on text content
    function setStatusColors() {
        // Get all elements with the class "status"
        const statusElements = document.querySelectorAll(".status");

        // Loop through each status element
        statusElements.forEach(function (element) {
            const statusText = element.textContent.trim(); // Get the text content of the element

            // Set the background color based on the status text
            switch (statusText) {
                case "Pending":
                    element.style.backgroundColor = "#007bff";
                    break;
                case "Approved":
                    element.style.backgroundColor = "#28a745";
                    break;
                case "Rejected":
                    element.style.backgroundColor = "#dc3545";
                    break;
                default:
                    // Default background color if the status text doesn't match
                    element.style.backgroundColor = "#d1d5db";
                    break;
            }
        });
    }

    // Call the function to set status colors when the page loads
    setStatusColors();
});      