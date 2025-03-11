// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
// Get references to the buttons and containers
const newButton = document.querySelector(".new");
const recordsButton = document.querySelector(".records");
const container1 = document.querySelector(".container-1");
const container2 = document.querySelector(".container-2");

// Set the "New" button to the active state by default
newButton.classList.add("active");

// Add event listeners to the buttons
newButton.addEventListener("click", function () {
// Only proceed if container-1 is not already displayed
if (container1.style.display !== "block") {
    // Fade in container-1 and hide container-2
    container1.style.display = "block";
    container1.style.opacity = 0;
    fadeIn(container1);

    container2.style.display = "none";

    // Add active class to new button
    newButton.classList.add("active");
    recordsButton.classList.remove("active");
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

    // Add active class to records button
    recordsButton.classList.add("active");
    newButton.classList.remove("active");
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

// Get all "Work Done" table cells
const workDoneCells = document.querySelectorAll("td:nth-child(3)");

workDoneCells.forEach(cell => {
    // Get the text content of the cell
    const text = cell.textContent;

    // Split the text by numbers (e.g., "1.", "2.", etc.)
    const points = text.split(/(\d+\.)/g).filter(Boolean);

    // Create a new HTML structure for the points
    let formattedText = "";
    for (let i = 0; i < points.length; i += 2) {
        const pointNumber = points[i]; // e.g., "1."
        const pointText = points[i + 1].trim(); // e.g., "Completed course on Java"
        formattedText += `<div>${pointNumber} ${pointText}</div>`;
    }

    // Update the cell's inner HTML with the formatted text
    cell.innerHTML = formattedText;
});

});      
