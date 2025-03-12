// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {

    // Get the table body element
    const tableBody = document.querySelector('table tbody');
    
    // Function to add remarks button to each table row
    function addRemarksButton() {
        // Get all table rows
        const tableRows = tableBody.querySelectorAll('tr');
    
        // Loop through each table row
        tableRows.forEach(function(row) {
            // Get the last table cell in the row
            const lastTableCell = row.querySelector('td:last-child');

            // Create a new remarks button element
            const remarksButton = document.createElement('span');
            remarksButton.className = 'remarks-btn';
            remarksButton.textContent = 'Remarks';

            // Append the remarks button to the last table cell
            lastTableCell.innerHTML = '';
            lastTableCell.appendChild(remarksButton);
        });
    }

    // Call the function to add remarks button to each table row
    addRemarksButton();

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
    const container1 = document.querySelector('.container-1');
    const container2 = document.querySelector('.container-2');
    const searchContainer = document.querySelector('.search-container');

    // Get the remarks button and close button
    const remarksBtn = document.querySelectorAll('.remarks-btn');
    const closeBtn = document.querySelector('.close-btn');

    // Get the form group elements
    const nameElement = document.querySelector('.form-group h4:nth-child(1)');
    const rollNoElement = document.querySelector('.form-group h4:nth-child(2)');
    const attendanceElement = document.querySelector('.form-group h4:nth-child(3)');

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

    // Function to switch containers
    function switchContainers() {
        container1.style.display = 'none';
        container2.style.display = 'block';
        container2.style.opacity = 0;
        fadeIn(container2);
        searchContainer.style.visibility = 'hidden';
    }

    // Function to fill form group details
    function fillDetails(name, rollNo, attendance) {
        const nameElement = document.querySelector('.form-group h4:nth-child(1)');
        const rollNoElement = document.querySelector('.form-group h4:nth-child(2)');
        const attendanceElement = document.querySelector('.form-group h4:nth-child(3)');

        nameElement.innerHTML = '<b>Name:</b> <span>' + name + '</span>';
        rollNoElement.innerHTML = '<b>Roll no:</b> <span>' + rollNo + '</span>';
        attendanceElement.innerHTML = '<b>Attendance(%):</b> <span>' + attendance + '</span>';
    }

    // Function to switch back to container 1
    function switchBack() {
        container2.style.display = 'none';
        container1.style.display = 'block';
        container1.style.opacity = 0;
        fadeIn(container1);
        searchContainer.style.visibility = 'visible';
    }

    // Add event listeners to remarks buttons
    remarksBtn.forEach((btn) => {
        btn.addEventListener('click', (e) => {
            // Get the table row data
            const rowData = e.target.parentNode.parentNode;
            const cells = rowData.cells;

            // Check if the table row has enough columns
            if (cells.length >= 4) {
                const name = cells[2].textContent;
                const rollNo = cells[1].textContent;
                const attendance = cells[3].textContent;

                // Fill form group details
                fillDetails(name, rollNo, attendance);

                // Switch containers
                switchContainers();
            } else {
                console.error('Table row does not have enough columns');
            }
        });
    });

    // Add event listener to close button
    closeBtn.addEventListener('click', switchBack);

});
