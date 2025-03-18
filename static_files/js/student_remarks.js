//static_files/js/student_remarks.js
document.addEventListener("DOMContentLoaded", function () {
  const table = document.querySelector(".section-remarks table");
  const sectionRemarks = document.querySelector(".section-remarks");
  const sectionEmpty = document.querySelector(".section-empty");

  // Check if table has data rows (more than just the header)
  if (table && table.rows.length > 1) {
    if (sectionRemarks) sectionRemarks.style.display = "block";
    if (sectionEmpty) sectionEmpty.style.display = "none";
  } else {
    if (sectionRemarks) sectionRemarks.style.display = "none";
    if (sectionEmpty) sectionEmpty.style.display = "block";
  }
});