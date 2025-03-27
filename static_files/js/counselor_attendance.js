// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {

    // Function to set status background colors based on text content
    function setStatusColors() {
    // Get all elements with the class "status"
    const statusElements = document.querySelectorAll(".status");
    
    // Loop through each status element
    statusElements.forEach(function (element) {
        const statusText = element.textContent.trim(); // Get the text content of the element
    
        // Set the background color based on the status text
        switch (statusText) {
            case "Present":
                element.style.backgroundColor = "#28a745";
                break;
            case "Absent":
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

    // Get the table body element
    const tableBody = document.querySelector('table tbody');
    
    // Get the search input element
    const searchInput = document.querySelector('.search-container input');
    
    // Function to search the table
    function searchTable() {
    // Get the search keyword
    const keyword = searchInput.value.trim().toLowerCase();
    
    // Get all table rows
    const tableRows = document.querySelectorAll('table tbody tr');
    
    // Loop through each table row
    tableRows.forEach(function(row) {
        // Get all table cells in the row
        const tableCells = row.querySelectorAll('td');
    
        // Initialize a flag to indicate if the row should be displayed
        let displayRow = false;
    
        // Loop through each table cell
        tableCells.forEach(function(cell) {
        // Get the text content of the cell
        const text = cell.textContent.trim().toLowerCase();
    
        // Check if the keyword is found in the cell text
        if (text.includes(keyword)) {
            displayRow = true;
        }
        });
    
        // Display or hide the row based on the flag
        if (displayRow) {
        row.style.display = 'table-row';
        } else {
        row.style.display = 'none';
        }
    });
    }
    
    // Function to reset the search
    function resetSearch() {
    // Get all table rows
    const tableRows = document.querySelectorAll('table tbody tr');
    
    // Loop through each table row
    tableRows.forEach(function(row) {
        // Display the row
        row.style.display = 'table-row';
    });
    }
    
    // Attach an event listener to the search input
    searchInput.addEventListener('input', searchTable);
    
    // Get the search icon element
    const searchIcon = document.querySelector('.search-icon');
    
    // Attach an event listener to the search icon
    searchIcon.addEventListener('click', searchTable);
    
    // Get the container elements
    const searchContainer = document.querySelector('.search-container');
    
    // Get the present and absent count elements
    const presentCountElement = document.querySelectorAll('.card .highlight')[0];
    const absentCountElement = document.querySelectorAll('.card .highlight')[1];

    // Initialize present and absent counts
    let presentCount = 0;
    let absentCount = 0;

    // Assuming you have a table with attendance data
    // Get the table body element
    // const tableBody = document.querySelector('tbody');

    // Iterate over each table row
    Array.from(tableBody.rows).forEach((row) => {
    // Get the status cell
    const statusCell = row.cells[5].textContent.trim();

    // Check if the student is present or absent
    if (statusCell === 'Present') {
        presentCount++;
    } else if (statusCell === 'Absent') {
        absentCount++;
    }
    });

    // Update the present and absent counts
    presentCountElement.textContent = presentCount.toString();
    absentCountElement.textContent = absentCount.toString();

});