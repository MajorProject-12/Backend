document.addEventListener('DOMContentLoaded', function() {
    const editButton = document.getElementById('editButton');
    const displayView = document.getElementById('displayView');
    const editView = document.getElementById('editView');
    const editProfileForm = document.getElementById('editProfileForm');

    editButton.addEventListener('click', function() {
        if (displayView.style.display !== 'none') {
            // Switch to edit mode
            displayView.style.display = 'none';
            editView.style.display = 'block';
            editButton.innerHTML = '<b>Save</b>';
            editButton.classList.add('save-button');
        } else {
            // Save changes
            editProfileForm.submit();
        }
    });
});