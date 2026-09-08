document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("toggleStatusBtn");
  const statusText = document.getElementById("jobStatus");
  const modal = document.getElementById("satisfactionModal");
  const generateBtn = document.getElementById("generateNoteBtn");
    if (!toggleBtn) return;

  const jobId = toggleBtn.dataset.jobId;
  const initialStatus = toggleBtn.dataset.initialStatus;

  toggleBtn.addEventListener("click", () => {
    fetch(`/jobs/${jobId}/toggle_status`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                alert("Failed to update job status");
                return;
            }

            const newStatus = data.new_status.toLowerCase();

            // Update status pill
            statusText.textContent = data.new_status;
            statusText.className = `status ${newStatus}`;

            // Update button text
            toggleBtn.textContent =
                newStatus === "open" ? "Complete Job" : "Reopen Job";

            if (newStatus === "complete") {
                modal.style.display = "flex";
            } else {
                location.reload();
            }
        });
});

  generateBtn.addEventListener("click", () => {
    window.open(
        `/jobs/${jobId}/satisfaction-note`,
        "_blank"
    );

    modal.style.display = "none";

    setTimeout(() => {
        location.reload();
    }, 500);
});


  window.addEventListener("click", e => {
    if (e.target === modal) modal.style.display = "none";
  });
});

