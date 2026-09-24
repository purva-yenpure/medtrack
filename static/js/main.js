// MedTrack Frontend JavaScript Utilities

document.addEventListener("DOMContentLoaded", () => {
  // 1. Role Toggle in Registration Form
  const roleSelect = document.getElementById("roleSelect");
  const patientFields = document.getElementById("patientFields");
  const doctorFields = document.getElementById("doctorFields");

  if (roleSelect && patientFields && doctorFields) {
    const toggleFields = () => {
      if (roleSelect.value === "Doctor") {
        doctorFields.style.display = "block";
        patientFields.style.display = "none";
      } else {
        doctorFields.style.display = "none";
        patientFields.style.display = "block";
      }
    };
    roleSelect.addEventListener("change", toggleFields);
    toggleFields();
  }

  // 2. Real-time Live Filter for Appointments Table
  const filterInput = document.getElementById("tableSearchInput");
  const appointmentsTable = document.getElementById("appointmentsTable");

  if (filterInput && appointmentsTable) {
    filterInput.addEventListener("keyup", () => {
      const term = filterInput.value.toLowerCase();
      const rows = appointmentsTable.querySelectorAll("tbody tr");
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? "" : "none";
      });
    });
  }

  // 3. Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert");
  if (alerts.length > 0) {
    setTimeout(() => {
      alerts.forEach(alert => {
        alert.style.transition = "opacity 0.5s ease";
        alert.style.opacity = "0";
        setTimeout(() => alert.remove(), 500);
      });
    }, 5000);
  }
});
