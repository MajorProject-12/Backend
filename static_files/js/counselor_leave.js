// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
  // Get references to the buttons and containers for toggling between "New" and "Records"
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

  // Make sure the dropdown selects take the proper values (useful when filtering)
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

  // Add animation to status changes
  const actionLinks = document.querySelectorAll('.action-link');
  actionLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      // Find the parent row
      const row = this.closest('tr');

      // Add a highlight effect
      row.style.transition = 'background-color 0.5s';
      row.style.backgroundColor = '#ffffcc';

      // Optional: Add a slight delay before redirecting
      // e.preventDefault();
      // setTimeout(() => {
      //   window.location.href = this.href;
      // }, 300);
    });
  });

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
  const yearSelect = document.getElementById('yearSelect');
  if (monthSelect && yearSelect) {
    monthSelect.addEventListener('change', function() {
      document.getElementById('searchForm').submit();
    });

    yearSelect.addEventListener('change', function() {
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