document.addEventListener("DOMContentLoaded", function () {

    const button = document.getElementById("generateProfitLossBtn");

    if (!button) {
        return;
    }

    button.addEventListener("click", function () {

        const reportUrl = this.dataset.reportUrl;

        if (!reportUrl) {
            console.error("Profit & Loss report URL is missing.");

            if (typeof showError === "function") {
                showError("Unable to generate the report.");
            }

            return;
        }

        const startDate = document.getElementById("reportStartDate").value;
        const endDate = document.getElementById("reportEndDate").value;
        const basis = document.getElementById("reportBasis").value;

        const params = new URLSearchParams();

        if (startDate) {
            params.append("start_date", startDate);
        }

        if (endDate) {
            params.append("end_date", endDate);
        }

        params.append("basis", basis || "Accrual");

        window.location.href = reportUrl + "?" + params.toString();
    });

});