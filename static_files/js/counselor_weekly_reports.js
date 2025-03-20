// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
    // Get references to the buttons and containers
    const newButton = document.querySelector(".new");
    const recordsButton = document.querySelector(".records");
    const container1 = document.querySelector(".container-1");
    const container2 = document.querySelector(".container-2");
    const monthYearSelector = document.querySelector(".month-year-selector");
    const searchInput = document.querySelector('#searchInput');
    const searchIcon = document.querySelector('.search-container .search-icon');
    const searchApiUrl = document.querySelector('#searchApiUrl').value;

    // Set the "New" button to the active state by default
    newButton.classList.add("active");

    // Show container-1 (This Week) by default
    container1.style.display = "block";
    container2.style.display = "none";
    monthYearSelector.style.display = "none";

    // Add event listeners to the buttons
    newButton.addEventListener("click", function () {
        // Only proceed if container-1 is not already displayed
        if (container1.style.display !== "block") {
            // Fade in container-1 and hide container-2
            container1.style.display = "block";
            container1.style.opacity = 0;
            fadeIn(container1);

            container2.style.display = "none";
            monthYearSelector.style.display = "none"; // Hide month-year-selector

            // Reset the search input
            searchInput.value = "";
            resetSearch();

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
            monthYearSelector.style.display = "flex"; // Show month-year-selector

            // Reset the search input
            searchInput.value = "";
            resetSearch();

            // Add active class to records button
            recordsButton.classList.add("active");
            newButton.classList.remove("active");
        }
    });

    // Add event listeners to the search input and search icon
    searchInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            searchReports();
        }
    });

    searchInput.addEventListener('input', function() {
        if (searchInput.value.trim() === "") {
            resetSearch();
        } else {
            searchReports();
        }
    });

    searchIcon.addEventListener('click', function() {
        searchReports();
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

    // Function to search reports using the API
    function searchReports() {
        const keyword = searchInput.value.trim();
        const month = document.getElementById('monthSelect').value;
        const year = document.getElementById('yearSelect').value;

        // Construct the API URL with query parameters
        let url = searchApiUrl + '?query=' + encodeURIComponent(keyword);

        if (month && month !== 'Select') {
            url += '&month=' + encodeURIComponent(month);
        }

        if (year && year !== 'Select') {
            url += '&year=' + encodeURIComponent(year);
        }

        // Make AJAX request to the API
        fetch(url)
            .then(response => response.json())
            .then(data => {
                // Get the appropriate table (this week or archive)
                const table = container1.style.display === 'block' ?
                    document.getElementById('this-week-table').querySelector('tbody') :
                    document.getElementById('archive-table').querySelector('tbody');

                // Clear the current table
                table.innerHTML = '';

                // If no reports found
                if (data.reports.length === 0) {
                    const row = document.createElement('tr');
                    const cell = document.createElement('td');
                    cell.setAttribute('colspan', '5');
                    cell.classList.add('text-center');
                    cell.textContent = 'No reports found matching your criteria.';
                    row.appendChild(cell);
                    table.appendChild(row);
                    return;
                }

                // Populate the table with the returned data
                data.reports.forEach(report => {
                    const row = document.createElement('tr');

                    // Create S.No cell
                    const snoCell = document.createElement('td');
                    snoCell.textContent = report.sno;
                    row.appendChild(snoCell);

                    // Create Date cell
                    const dateCell = document.createElement('td');
                    dateCell.textContent = report.date;
                    row.appendChild(dateCell);

                    // Create Roll No cell
                    const rollNoCell = document.createElement('td');
                    rollNoCell.textContent = report.roll_no;
                    row.appendChild(rollNoCell);

                    // Create Student Name cell
                    const nameCell = document.createElement('td');
                    nameCell.textContent = report.student_name;
                    row.appendChild(nameCell);

                    // Create Work Done cell
                    const workDoneCell = document.createElement('td');
                    formatWorkDone(workDoneCell, report.work_done);
                    row.appendChild(workDoneCell);

                    // Add the row to the table
                    table.appendChild(row);
                });
            })
            .catch(error => {
                console.error('Error searching reports:', error);
            });
    }

    // Function to reset the search (display all rows)
    function resetSearch() {
        // Reset search is now handled by the searchReports function with empty parameters
        if (container2.style.display === 'block') {
            // Only refresh search if in archive view
            const month = document.getElementById('monthSelect').value;
            const year = document.getElementById('yearSelect').value;

            if (month !== 'Select' || year !== 'Select') {
                searchReports();
            }
        }
    }

    // Get all "Work Done" table cells
    const workDoneCells = document.querySelectorAll("td:nth-child(5)");

    workDoneCells.forEach(cell => {
        formatWorkDone(cell, cell.textContent);
    });

    // Function to format work done text with numbered points
    function formatWorkDone(cell, text) {
        // Split the text by numbers (e.g., "1.", "2.", etc.)
        const points = text.split(/(\d+\.)/g).filter(Boolean);

        // Create a new HTML structure for the points
        let formattedText = "";
        for (let i = 0; i < points.length; i += 2) {
            if (i + 1 < points.length) {
                const pointNumber = points[i]; // e.g., "1."
                const pointText = points[i + 1].trim(); // e.g., "Completed course on Java"
                formattedText += `<div>${pointNumber} ${pointText}</div>`;
            } else {
                // Handle odd number of elements
                formattedText += `<div>${points[i]}</div>`;
            }
        }

        // If no points were found, just use the original text
        if (formattedText === "") {
            formattedText = text;
        }

        // Update the cell's inner HTML with the formatted text
        cell.innerHTML = formattedText;
    }

    // Populate the year dropdown with a range of years
    const yearSelect = document.getElementById('yearSelect');
    const currentYear = new Date().getFullYear();
    const startYear = currentYear - 10; // 10 years ago

    for (let year = currentYear; year >= startYear; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }

    // Get references to the month and year dropdowns
    const monthSelect = document.getElementById('monthSelect');

    // Add event listeners to the month and year dropdowns
    monthSelect.addEventListener('change', function() {
        searchReports();
    });

    yearSelect.addEventListener('change', function() {
        searchReports();
    });
});