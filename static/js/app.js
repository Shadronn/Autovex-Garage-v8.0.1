/* =========================================================
   DASHBOARD JAVASCRIPT
   ========================================================= */


/* =========================================================
   SIDEBAR
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const sidebar = document.getElementById("sidebar");
    const toggleBtn = document.getElementById("toggleSidebar");

    if (sidebar && toggleBtn) {

        toggleBtn.addEventListener("click", function () {

            sidebar.classList.toggle("collapsed");
            sidebar.classList.toggle("open");

        });

    }


    /* =====================================================
       DROPDOWNS
       ===================================================== */

    const dropdowns = document.querySelectorAll(".dropdown");

    dropdowns.forEach(dropdown => {

        const button = dropdown.querySelector(".dropdown-btn");

        if (!button) {
            return;
        }

        button.addEventListener("click", function () {

            dropdowns.forEach(item => {

                if (item !== dropdown) {
                    item.classList.remove("active");
                }

            });

            dropdown.classList.toggle("active");

        });

    });


    /* =====================================================
       TABLE PAGINATION
       ===================================================== */

    const tableBody = document.getElementById("tableBody");

    if (tableBody) {

        const rows = tableBody.getElementsByTagName("tr");

        const rowsPerPage = 20;

        const totalPages = Math.ceil(
            rows.length / rowsPerPage
        );

        let currentPage = 1;


        function displayPage(page) {

            for (let i = 0; i < rows.length; i++) {

                if (
                    i >= (page - 1) * rowsPerPage &&
                    i < page * rowsPerPage
                ) {

                    rows[i].style.display = "table-row";

                } else {

                    rows[i].style.display = "none";

                }

            }

        }


        function setupPagination() {

            const wrapper =
                document.getElementById("pagination");

            if (!wrapper) {
                return;
            }

            wrapper.innerHTML = "";

            if (totalPages <= 1) {
                return;
            }

            for (
                let i = 1;
                i <= totalPages;
                i++
            ) {

                const btn =
                    document.createElement("button");

                btn.type = "button";

                btn.innerText = i;

                if (i === currentPage) {
                    btn.classList.add("active");
                }

                btn.addEventListener("click", function () {

                    currentPage = i;

                    displayPage(currentPage);

                    wrapper
                        .querySelectorAll("button")
                        .forEach(button => {
                            button.classList.remove("active");
                        });

                    this.classList.add("active");

                });

                wrapper.appendChild(btn);

            }

        }


        displayPage(currentPage);

        setupPagination();

    }


    /* =========================================================
       DASHBOARD TABS
       ========================================================= */

    const dashboardTabs =
        document.querySelectorAll(".dashboard-tab");

    const tabContents =
        document.querySelectorAll(".tab-content");


    dashboardTabs.forEach(tab => {

        tab.addEventListener("click", function () {

            const tabName =
                this.dataset.tab;

            if (!tabName) {
                return;
            }


            /* -----------------------------------------------
               Active tab
               ----------------------------------------------- */

            dashboardTabs.forEach(item => {

                item.classList.remove("active");

            });

            this.classList.add("active");


            /* -----------------------------------------------
               Hide all tab contents
               ----------------------------------------------- */

            tabContents.forEach(content => {

                content.classList.remove("active");

            });


            /* -----------------------------------------------
               Show selected tab
               ----------------------------------------------- */

            const selectedContent =
                document.getElementById(tabName);

            if (selectedContent) {

                selectedContent.classList.add("active");

            }


            /* -----------------------------------------------
               Financials opened
               ----------------------------------------------- */

            if (tabName === "financials") {

                resetFinancials();

            }


            /* -----------------------------------------------
               Back to Dashboard
               ----------------------------------------------- */

            if (tabName === "dashboard") {

                resetFinancials();

                const jobs =
                    document.getElementById("jobs");

                if (jobs) {

                    jobs.classList.add("active");

                }

            }

        });

    });


    /* =========================================================
       FINANCIAL ELEMENTS
       ========================================================= */

    const workshopCard =
        document.getElementById("workshopCard");

    const financialSummary =
        document.getElementById("financialSummary");

    const financialOverview =
        document.getElementById("financialOverview");

    const recentPayments =
        document.getElementById("recentPayments");

    const financialDetails =
        document.getElementById("financialDetails");

    const financialEmptyState =
        document.getElementById("financialEmptyState");

    const revenueList =
        document.getElementById("revenueList");

    const debtList =
        document.getElementById("debtList");

    const pendingList =
        document.getElementById("pendingList");

    const overdueList =
        document.getElementById("overdueList");

    const financialCards =
        document.querySelectorAll(
            ".financial-card-clickable"
        );


    /* =========================================================
       HIDE FINANCIAL DETAIL LISTS
       ========================================================= */

    function hideFinancialLists() {

        if (revenueList) {
            revenueList.style.display = "none";
        }

        if (debtList) {
            debtList.style.display = "none";
        }

        if (pendingList) {
            pendingList.style.display = "none";
        }

        if (overdueList) {
            overdueList.style.display = "none";
        }

    }


    /* =========================================================
       RESET FINANCIALS
       ========================================================= */

    function resetFinancials() {

        /*
         * Show workshop card
         */

        if (workshopCard) {
            workshopCard.style.display = "";
        }


        /*
         * Show financial summary
         */

        if (financialSummary) {
            financialSummary.style.display = "";
        }


        /*
         * Show overview
         */

        if (financialOverview) {
            financialOverview.style.display = "";
        }


        /*
         * Show recent payments
         */

        if (recentPayments) {
            recentPayments.style.display = "";
        }


        /*
         * Hide detail container
         */

        if (financialDetails) {
            financialDetails.style.display = "none";
        }


        /*
         * Hide empty state
         */

        if (financialEmptyState) {
            financialEmptyState.style.display = "none";
        }


        /*
         * Hide all lists
         */

        hideFinancialLists();


        /*
         * Remove selected state from financial cards
         */

        financialCards.forEach(card => {

            card.classList.remove("active");

        });

    }


    /* =========================================================
       OPEN FINANCIAL DETAIL
       ========================================================= */

    function openFinancialDetail(view) {

        /*
         * Hide workshop card
         */

        if (workshopCard) {
            workshopCard.style.display = "none";
        }


        /*
         * Keep financial summary visible
         *
         * The summary cards remain available so the
         * user can switch between Revenue and Debt.
         */

        if (financialSummary) {
            financialSummary.style.display = "";
        }


        /*
         * Hide overview
         */

        if (financialOverview) {
            financialOverview.style.display = "none";
        }


        /*
         * Hide recent payments
         */

        if (recentPayments) {
            recentPayments.style.display = "none";
        }


        /*
         * Show detail container
         */

        if (financialDetails) {
            financialDetails.style.display = "block";
        }


        /*
         * Hide all lists
         */

        hideFinancialLists();


        /*
         * Show selected list
         */

        if (view === "revenue") {

            if (revenueList) {
                revenueList.style.display = "block";
            }

        }

        else if (view === "debt") {

            if (debtList) {
                debtList.style.display = "block";
            }

        }

        else if (view === "pending") {

            if (pendingList) {
                pendingList.style.display = "block";
            }

        }

        else if (view === "overdue") {

            if (overdueList) {
                overdueList.style.display = "block";
            }

        }


        /*
         * Highlight selected card
         */

        financialCards.forEach(card => {

            card.classList.remove("active");

        });

        financialCards.forEach(card => {

            if (
                card.dataset.financialView === view
            ) {

                card.classList.add("active");

            }

        });

    }


    /* =========================================================
       FINANCIAL CARD CLICKS
       ========================================================= */

    financialCards.forEach(card => {

        card.addEventListener("click", function (event) {

            event.preventDefault();

            const view =
                this.dataset.financialView;

            if (!view) {
                return;
            }

            openFinancialDetail(view);

        });

    });


    /* =========================================================
       BACK TO DASHBOARD BUTTON
       ========================================================= */

    const backToDashboard =
        document.getElementById("backToDashboard");


    if (backToDashboard) {

        backToDashboard.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                resetFinancials();


                /*
                 * Activate Jobs tab
                 */

                dashboardTabs.forEach(tab => {

                    tab.classList.remove("active");

                });


                const dashboardTab =
                    document.querySelector(
                        '.dashboard-tab[data-tab="dashboard"]'
                    );

                if (dashboardTab) {

                    dashboardTab.classList.add("active");

                }


                const jobs =
                    document.getElementById("jobs");

                if (jobs) {

                    tabContents.forEach(content => {

                        content.classList.remove("active");

                    });

                    jobs.classList.add("active");

                }

            }
        );

    }


    /* =========================================================
       OPTIONAL: FINANCIAL DETAIL BACK BUTTONS
       ========================================================= */

    const financialBackButtons =
        document.querySelectorAll(
            "[data-financial-back]"
        );


    financialBackButtons.forEach(button => {

        button.addEventListener("click", function (event) {

            event.preventDefault();

            resetFinancials();

        });

    });


    /* =========================================================
       INITIAL FINANCIAL STATE
       ========================================================= */

    /*
     * Only reset financial elements if the page actually
     * contains the Financials section.
     */

    if (
        financialOverview ||
        financialSummary ||
        financialCards.length
    ) {

        resetFinancials();

    }

});

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const exportBtn =
            document.getElementById(
                "exportPaymentsBtn"
            );


        if (!exportBtn) {
            return;
        }


        exportBtn.addEventListener(
            "click",
            function () {

                const exportUrl =
                    this.dataset.exportUrl;


                const search =
                    document.getElementById(
                        "paymentSearch"
                    ).value;


                const paymentType =
                    document.getElementById(
                        "paymentType"
                    ).value;


                const paymentMethod =
                    document.getElementById(
                        "paymentMethod"
                    ).value;


                const period =
                    document.getElementById(
                        "paymentPeriod"
                    ).value;


                const params =
                    new URLSearchParams({

                        search: search,

                        payment_type:
                            paymentType,

                        payment_method:
                            paymentMethod,

                        period: period

                    });


                window.location.href =
                    exportUrl
                    + "?"
                    + params.toString();

            }
        );

    }
);


document.addEventListener(
    "DOMContentLoaded",
    function () {

        const searchInput =
            document.getElementById(
                "paymentSearch"
            );

        const typeSelect =
            document.getElementById(
                "paymentType"
            );

        const methodSelect =
            document.getElementById(
                "paymentMethod"
            );

        const periodSelect =
            document.getElementById(
                "paymentPeriod"
            );

        const tableBody =
            document.getElementById(
                "paymentsTableBody"
            );


        if (
            !searchInput ||
            !typeSelect ||
            !methodSelect ||
            !periodSelect ||
            !tableBody
        ) {

            return;

        }


        function getPeriodStart(period) {

            const now = new Date();

            if (period === "Today") {

                return new Date(
                    now.getFullYear(),
                    now.getMonth(),
                    now.getDate()
                );

            }


            if (period === "This Week") {

                const date =
                    new Date(now);

                const day =
                    date.getDay();

                const difference =
                    day === 0
                        ? 6
                        : day - 1;

                date.setDate(
                    date.getDate()
                    - difference
                );

                date.setHours(
                    0,
                    0,
                    0,
                    0
                );

                return date;

            }


            if (period === "This Month") {

                return new Date(
                    now.getFullYear(),
                    now.getMonth(),
                    1
                );

            }


            if (period === "This Quarter") {

                const quarter =
                    Math.floor(
                        now.getMonth() / 3
                    );

                return new Date(
                    now.getFullYear(),
                    quarter * 3,
                    1
                );

            }


            if (period === "This Year") {

                return new Date(
                    now.getFullYear(),
                    0,
                    1
                );

            }


            return null;

        }


        function applyPaymentFilters() {

            const search =
                searchInput.value
                    .trim()
                    .toLowerCase();


            const selectedType =
                typeSelect.value
                    .trim()
                    .toLowerCase();


            const selectedMethod =
                methodSelect.value
                    .trim()
                    .toLowerCase();


            const selectedPeriod =
                periodSelect.value;


            const periodStart =
                getPeriodStart(
                    selectedPeriod
                );


            const rows =
                tableBody.querySelectorAll(
                    "tr[data-payment-type]"
                );


            rows.forEach(
                function (row) {

                    const type =
                        (
                            row.dataset
                                .paymentType
                            || ""
                        ).toLowerCase();


                    const method =
                        (
                            row.dataset
                                .paymentMethod
                            || ""
                        ).toLowerCase();


                    const dateString =
                        row.dataset
                            .paymentDate;


                    const searchableText =
                        row.textContent
                            .toLowerCase();


                    let visible = true;


                    /*
                     * SEARCH
                     */

                    if (
                        search &&
                        !searchableText.includes(
                            search
                        )
                    ) {

                        visible = false;

                    }


                    /*
                     * PAYMENT TYPE
                     */

                    if (
                        selectedType &&
                        type !== selectedType
                    ) {

                        visible = false;

                    }


                    /*
                     * PAYMENT METHOD
                     */

                    if (
                        selectedMethod &&
                        method !== selectedMethod
                    ) {

                        visible = false;

                    }


                    /*
                     * PERIOD
                     */

                    if (
                        visible &&
                        periodStart &&
                        dateString
                    ) {

                        const paymentDate =
                            new Date(
                                dateString
                            );


                        if (
                            paymentDate
                            < periodStart
                        ) {

                            visible = false;

                        }

                    }


                    row.style.display =
                        visible
                            ? ""
                            : "none";

                }
            );

        }


        searchInput.addEventListener(
            "input",
            applyPaymentFilters
        );


        typeSelect.addEventListener(
            "change",
            applyPaymentFilters
        );


        methodSelect.addEventListener(
            "change",
            applyPaymentFilters
        );


        periodSelect.addEventListener(
            "change",
            applyPaymentFilters
        );

    }
);

