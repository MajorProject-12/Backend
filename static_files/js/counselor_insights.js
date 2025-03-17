//counselor_insights.js
document.addEventListener("DOMContentLoaded", function () {
    // Client-side search filtering on the table (if needed)
    const searchInput = document.querySelector('.search-container input');
    function searchTable() {
        const keyword = searchInput.value.trim().toLowerCase();
        const tableRows = document.querySelectorAll('table tbody tr');
        tableRows.forEach(function(row) {
            let displayRow = false;
            row.querySelectorAll('td').forEach(function(cell) {
                if(cell.textContent.trim().toLowerCase().includes(keyword)) {
                    displayRow = true;
                }
            });
            row.style.display = displayRow ? 'table-row' : 'none';
        });
    }
    searchInput.addEventListener('input', searchTable);
    const searchIcon = document.querySelector('.search-icon');
    if(searchIcon) {
        searchIcon.addEventListener('click', searchTable);
    }

    // Handle inline remark form toggle
    const remarksBtns = document.querySelectorAll('.btn-add-remark');
    const container1 = document.querySelector('.container-1');
    const container2 = document.querySelector('.container-2');
    const closeBtn = document.querySelector('.close-btn');

    // Function to fade in element
    function fadeIn(element) {
        let opacity = 0;
        element.style.opacity = 0;
        element.style.display = 'block';
        const interval = setInterval(function () {
            if (opacity < 1) {
                opacity += 0.2;
                element.style.opacity = opacity;
            } else {
                clearInterval(interval);
            }
        }, 50);
    }

    // Switch to remark form container
    function switchContainers() {
        container1.style.display = 'none';
        fadeIn(container2);
    }

    // Switch back to student list
    function switchBack() {
        container2.style.display = 'none';
        fadeIn(container1);
    }

    // Add event listeners to remark buttons
    remarksBtns.forEach((btn) => {
        btn.addEventListener('click', (e) => {
            const rollNo = btn.getAttribute('data-roll');
            const name = btn.getAttribute('data-name');
            const attendance = btn.getAttribute('data-attendance');

            // Set hidden input value and update display texts
            document.getElementById('student_id').value = rollNo;
            document.getElementById('name-display').querySelector('span').textContent = name;
            document.getElementById('rollno-display').querySelector('span').textContent = rollNo;
            document.getElementById('attendance-display').querySelector('span').textContent = attendance;

            switchContainers();
        });
    });

    closeBtn.addEventListener('click', switchBack);
});
