document.addEventListener("DOMContentLoaded", function () {
    // Handle inline remark form toggle
    const remarksBtns = document.querySelectorAll('.btn-add-remark');
    const container1 = document.querySelector('.container-1');
    const container2 = document.querySelector('.container-2');
    const closeBtn = document.querySelector('.close-btn');
    const resetBtn = document.querySelector('.reset-btn');
    
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
    function switchToRemarkForm() {
        container1.style.display = 'none';
        fadeIn(container2);
    }
    
    // Switch back to student list
    function switchToStudentList() {
        container2.style.display = 'none';
        fadeIn(container1);
    }
    
    // Add event listeners to remark buttons
    remarksBtns.forEach((btn) => {
        btn.addEventListener('click', (e) => {
            const rollNo = btn.getAttribute('data-roll');
            const name = btn.getAttribute('data-name');
            const attendance = btn.getAttribute('data-attendance');
            
            console.log("Adding remark for:", rollNo, name, attendance);

            // Set hidden input value and update display texts
            document.getElementById('student_id').value = rollNo;
            document.getElementById('name-display').querySelector('span').textContent = name;
            document.getElementById('rollno-display').querySelector('span').textContent = rollNo;
            document.getElementById('attendance-display').querySelector('span').textContent = attendance;

            // Clear any previous remark text
            document.getElementById('remarks').value = '';

            switchToRemarkForm();
        });
    });

    // Close button listener
    if (closeBtn) {
        closeBtn.addEventListener('click', switchToStudentList);
    }

    // Reset button listener - keep the form open but clear fields
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            document.getElementById('remarks').value = '';
        });
    }

    // Debug: Log if the form submission is happening
    const form = document.querySelector('.container-2 form');
    if (form) {
        form.addEventListener('submit', function(e) {
            console.log("Form submitting with student ID:", document.getElementById('student_id').value);
            console.log("Remarks:", document.getElementById('remarks').value);
        });
    }
});