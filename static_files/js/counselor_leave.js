// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
  // Get references to the buttons and containers
  const newButton = document.querySelector(".new");
  const recordsButton = document.querySelector(".records");
  const container1 = document.querySelector(".container-1");
  const container2 = document.querySelector(".container-2");
  const monthYearSelector = document.querySelector(".month-year-selector");
  const searchInput = document.querySelector('.search-container input');

  // Set the "New" button to the active state by default
  newButton.classList.add("active");
  container1.style.display = "block";
  container2.style.display = "none";
  monthYearSelector.style.display = "none";

  // Toggle between container-1 (Pending) and container-2 (Processed Records)
  newButton.addEventListener("click", function () {
    if (container1.style.display !== "block") {
      container1.style.display = "block";
      container1.style.opacity = 0;
      fadeIn(container1);
      container2.style.display = "none";
      monthYearSelector.style.display = "none";
      newButton.classList.add("active");
      recordsButton.classList.remove("active");
    }
  });

  recordsButton.addEventListener("click", function () {
    if (container2.style.display !== "block") {
      container2.style.display = "block";
      container2.style.opacity = 0;
      fadeIn(container2);
      container1.style.display = "none";
      monthYearSelector.style.display = "flex";
      recordsButton.classList.add("active");
      newButton.classList.remove("active");
    }
  });

  // Fade in utility function
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

  // Populate the year dropdown
  const yearSelect = document.getElementById('yearSelect');
  if (yearSelect) {
    const currentYear = new Date().getFullYear();
    const startYear = currentYear - 10;
    for (let year = currentYear; year >= startYear; year--) {
      const option = document.createElement('option');
      option.value = year;
      option.textContent = year;
      yearSelect.appendChild(option);
    }
  }

  // Set dropdown values from URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('month')) {
    const monthValue = urlParams.get('month');
    const monthSelect = document.getElementById('monthSelect');
    if (monthSelect) {
      monthSelect.value = monthValue;
    }
  }
  if (urlParams.has('year')) {
    const yearValue = urlParams.get('year');
    const yearSelect = document.getElementById('yearSelect');
    if (yearSelect) {
      yearSelect.value = yearValue;
    }
  }

  // Handle action links (approve/reject) with improved error handling
  const actionLinks = document.querySelectorAll('.action-link');
  actionLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();

      // Find the parent row
      const row = this.closest('tr');

      // Add a highlight effect
      row.style.transition = 'background-color 0.5s';
      row.style.backgroundColor = '#ffffcc';

      // Get leave ID and status from the URL
      const url = this.getAttribute('href');
      const leaveId = new URL(url, window.location.origin).searchParams.get('leave_id');
      const status = new URL(url, window.location.origin).searchParams.get('status');

      // Add CSRF token to headers if Django is expecting it
      const csrfToken = getCookie('csrftoken');

      // Use Fetch API instead of XMLHttpRequest
      fetch(url, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken
        }
      })
      .then(response => {
        // First check if the response is JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return response.json().then(data => {
            if (!response.ok) {
              throw new Error(data.message || 'Server error');
            }
            return data;
          });
        } else {
          // If not JSON, it might be a redirect or HTML
          if (response.ok) {
            // Just reload the page to follow any redirects
            window.location.reload();
            return null;
          } else {
            throw new Error('Server returned an error');
          }
        }
      })
      .then(data => {
        if (data) {
          // Update UI if we got JSON data back
          updateUI(row, status);
        }
      })
      .catch(error => {
        // Display error message
        console.error('Error:', error);
        alert('Error: ' + error.message);

        // Reset row highlighting
        row.style.backgroundColor = '';
      });
    });
  });

  // Helper function to get cookies (for CSRF token)
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Function to update UI after successful action
  function updateUI(row, status) {
    // Update the status in the current row
    const statusCell = row.querySelector('.status');
    if (statusCell) {
      statusCell.textContent = status;
      statusCell.className = 'status ' + status.toLowerCase();

      // Update status color
      if (status === 'Approved') {
        statusCell.style.backgroundColor = '#28a745';
      } else {
        statusCell.style.backgroundColor = '#dc3545';
      }
    }

    // Remove operation buttons
    const operationsCell = row.querySelector('.operations');
    if (operationsCell) {
      operationsCell.innerHTML = '';
    }

    // After a delay, move the row to the processed table
    setTimeout(() => {
      const processedTable = container2.querySelector('tbody');

      // Remove the row from pending table
      row.remove();

      // Check if pending table is now empty
      const pendingRows = container1.querySelectorAll('tbody tr');
      if (pendingRows.length === 0 || (pendingRows.length === 1 && pendingRows[0].querySelector('td[colspan]'))) {
        // No rows left, add a "no pending applications" row
        const pendingTbody = container1.querySelector('tbody');
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="8" class="text-center">No pending leave applications.</td>';
        pendingTbody.appendChild(emptyRow);
      }

      // Switch to Records tab
      recordsButton.click();

      // Reload page to get updated records
      window.location.reload();
    }, 1000);
  }

  // Set status colors for all status elements
  setStatusColors();

  // Function to set status colors based on text content
  function setStatusColors() {
    const statusElements = document.querySelectorAll(".status");
    statusElements.forEach(function (element) {
      const statusText = element.textContent.trim();
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
          element.style.backgroundColor = "#d1d5db";
          break;
      }
    });
  }

  // Auto-submit form when month/year selection changes
  const monthSelect = document.getElementById('monthSelect');
  const yearSelectForChange = document.getElementById('yearSelect');
  if (monthSelect && yearSelectForChange) {
    monthSelect.addEventListener('change', function() {
      document.getElementById('searchForm').submit();
    });

    yearSelectForChange.addEventListener('change', function() {
      document.getElementById('searchForm').submit();
    });
  }

  // Auto-submit search form when typing stops
  if (searchInput) {
    let typingTimer;
    const doneTypingInterval = 500; // ms

    searchInput.addEventListener('keyup', function() {
      clearTimeout(typingTimer);
      if (searchInput.value) {
        typingTimer = setTimeout(function() {
          document.getElementById('searchForm').submit();
        }, doneTypingInterval);
      }
    });
  }
});