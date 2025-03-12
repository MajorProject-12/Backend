// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
  // Get references to the buttons and containers for toggling between "New" and "Records"
  const newButton = document.querySelector(".new");
  const recordsButton = document.querySelector(".records");
  const container1 = document.querySelector(".container-1");
  const container2 = document.querySelector(".container-2");
  const monthYearSelector = document.querySelector(".month-year-selector");
  const searchInput = document.querySelector('.search-container input');
  const searchIcon = document.querySelector('.search-container .search-icon');

  // Set the "New" button to the active state by default
  newButton.classList.add("active");

  // Toggle between container-1 (New) and container-2 (Records)
  newButton.addEventListener("click", function () {
    if (container1.style.display !== "block") {
      container1.style.display = "block";
      container1.style.opacity = 0;
      fadeIn(container1);
      container2.style.display = "none";
      monthYearSelector.style.display = "none";
      searchInput.value = "";
      resetSearch();
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
      searchInput.value = "";
      resetSearch();
      recordsButton.classList.add("active");
      newButton.classList.remove("active");
    }
  });

  // Search functionality
  searchInput.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
      searchTable();
    }
  });
  searchInput.addEventListener('input', function() {
    if (searchInput.value.trim() === "") {
      resetSearch();
    } else {
      searchTable();
    }
  });
  searchIcon.addEventListener('click', function() {
    searchTable();
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

  // Search the table
  function searchTable() {
    const keyword = searchInput.value.trim().toLowerCase();
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(function(row) {
      const tableCells = row.querySelectorAll('td');
      let displayRow = false;
      tableCells.forEach(function(cell) {
        const text = cell.textContent.trim().toLowerCase();
        if (text.includes(keyword)) {
          displayRow = true;
        }
      });
      row.style.display = displayRow ? 'table-row' : 'none';
    });
  }

  // Reset search function
  function resetSearch() {
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(function(row) {
      row.style.display = 'table-row';
    });
  }

  // Populate the year dropdown
  const yearSelect = document.getElementById('yearSelect');
  const currentYear = new Date().getFullYear();
  const startYear = currentYear - 10;
  for (let year = currentYear; year >= startYear; year--) {
    const option = document.createElement('option');
    option.value = year;
    option.textContent = year;
    yearSelect.appendChild(option);
  }

  // Month/Year filtering
  const monthSelect = document.getElementById('monthSelect');
  monthSelect.addEventListener('change', filterTable);
  yearSelect.addEventListener('change', filterTable);
  function filterTable() {
    const selectedMonth = monthSelect.value;
    const selectedYear = yearSelect.value;
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(function(row) {
      const dateCell = row.querySelector('td:nth-child(2)');
      if (!dateCell) return;
      const dateText = dateCell.textContent;
      const dateParts = dateText.split('/');
      const month = dateParts[1];
      const year = dateParts[2];
      let displayRow = true;
      if (selectedMonth !== "Select" && month !== selectedMonth) {
        displayRow = false;
      }
      if (selectedYear !== "Select" && year !== selectedYear) {
        displayRow = false;
      }
      row.style.display = displayRow ? 'table-row' : 'none';
    });
  }

  // Set status colors based on text content
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
  setStatusColors();

  // Update status colors
  function updateStatusColors() {
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

  // Attach event listeners to operation buttons
  function setOperations() {
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(function(row) {
      const cells = row.querySelectorAll('td');
      // Skip if this row doesn't have an operations column (i.e. fewer than 8 cells)
      if (cells.length < 8) return;
      const statusCell = cells[6]; // 7th cell (0-indexed)
      const operationsCell = cells[7]; // 8th cell

      // Get initial status
      const statusElement = statusCell.querySelector('.status');
      const initialStatus = statusElement ? statusElement.textContent.trim() : '';

      // Configure operations cell based on current status
      updateOperationsCell(operationsCell, statusCell, initialStatus);
    });
  }

  // Function to update operations cell based on status
  function updateOperationsCell(operationsCell, statusCell, status) {
    // Clear existing content
    operationsCell.innerHTML = '';

    if (status === 'Pending') {
      // For pending status, show approve/reject buttons
      operationsCell.innerHTML = `
        <div class="operations-1">
          <button class="approve" title="Approve">
            <img src="/static/images/icons/Approve.svg" alt="Approve">
          </button>
          <button class="reject" title="Reject">
            <img src="/static/images/icons/Reject.svg" alt="Reject">
          </button>
        </div>
      `;

      // Add event listeners to buttons
      const approveButton = operationsCell.querySelector('.approve');
      const rejectButton = operationsCell.querySelector('.reject');

      approveButton.addEventListener('click', function() {
        statusCell.innerHTML = '<span class="status approved">Approved</span>';
        updateStatusColors();
        updateOperationsCell(operationsCell, statusCell, 'Approved');
      });

      rejectButton.addEventListener('click', function() {
        statusCell.innerHTML = '<span class="status rejected">Rejected</span>';
        updateStatusColors();
        updateOperationsCell(operationsCell, statusCell, 'Rejected');
      });
    } else if (status === 'Approved' || status === 'Rejected') {
      // For approved/rejected status, show reset button
      operationsCell.innerHTML = `
        <div class="operations-2">
          <button class="reset" title="Reset">
            <img src="/static/images/icons/Reset-status.svg" alt="Reset">
          </button>
          Reset
        </div>
      `;

      // Add event listener to reset button
      const resetButton = operationsCell.querySelector('.reset');
      resetButton.addEventListener('click', function() {
        statusCell.innerHTML = '<span class="status pending">Pending</span>';
        updateStatusColors();
        updateOperationsCell(operationsCell, statusCell, 'Pending');
      });
    }
  }

  // Initialize operations
  setOperations();
});