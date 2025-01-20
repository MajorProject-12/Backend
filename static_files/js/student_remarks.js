document.addEventListener("DOMContentLoaded", function () {
    // Get references to the table, section-remarks, and section-empty
    const table = document.querySelector(".section-remarks table");
    const sectionRemarks = document.querySelector(".section-remarks");
    const sectionEmpty = document.querySelector(".section-empty");

    // Check if the table has rows (excluding the header row)
    if (table && table.rows.length > 1) {
        // If data is available, show the table and hide the empty section
        sectionRemarks.style.display = "block";
        sectionEmpty.style.display = "none";
    } else {
        // If no data is available, hide the table and show the empty section
        sectionRemarks.style.display = "none";
        sectionEmpty.style.display = "block";
    }
});