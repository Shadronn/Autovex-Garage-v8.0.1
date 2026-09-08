/* =========================================================
   AUTOVEX FINANCIALS
   Complete Financials JavaScript
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       ELEMENT HELPERS
       ===================================================== */

    const $ = (selector) => {
        return document.querySelector(selector);
    };

    const $$ = (selector) => {
        return document.querySelectorAll(selector);
    };


    /* =====================================================
       FINANCIAL TABS
       ===================================================== */

    const tabs = $$("[data-financial-tab]");
    const contents = $$(".financial-module-tab");


    function activateFinancialTab(tabId, updateUrl = true) {

        if (!tabId) {
            return;
        }


        let selectedTab = null;

        tabs.forEach(function (tab) {

            const isActive =
                tab.dataset.financialTab === tabId;

            tab.classList.toggle(
                "active",
                isActive
            );

            if (isActive) {
                selectedTab = tab;
            }

        });


        contents.forEach(function (content) {

            content.classList.toggle(
                "active",
                content.id === tabId
            );

        });


        /*
         * If the requested tab does not exist,
         * fall back to the first available tab.
         */

        if (!selectedTab && tabs.length > 0) {

            const firstTab = tabs[0];

            const firstTabId =
                firstTab.dataset.financialTab;

            firstTab.classList.add("active");

            const firstContent =
                document.getElementById(firstTabId);

            if (firstContent) {
                firstContent.classList.add("active");
            }

            tabId = firstTabId;
        }


        /*
         * Keep the selected tab in the URL.
         *
         * This is what allows:
         *
         * /financials?tab=expenses
         *
         * to open directly on Expenses.
         */

        if (updateUrl) {

            const url =
                new URL(window.location.href);

            url.searchParams.set(
                "tab",
                tabId
            );

            window.history.replaceState(
                {},
                "",
                url
            );

        }

    }


    tabs.forEach(function (tab) {

        tab.addEventListener(
            "click",
            function () {

                const target =
                    this.dataset.financialTab;

                activateFinancialTab(
                    target,
                    true
                );

            }
        );

    });


    /*
     * Activate tab from URL.
     *
     * Example:
     *
     * /financials?tab=expenses
     */

    const urlParams =
        new URLSearchParams(
            window.location.search
        );

    const requestedTab =
        urlParams.get("tab");


    if (requestedTab) {

        activateFinancialTab(
            requestedTab,
            false
        );

    } else if (tabs.length > 0) {

        /*
         * If no tab is specified,
         * preserve whatever the HTML has marked
         * active. Otherwise use the first tab.
         */

        const existingActive =
            Array.from(tabs).find(
                tab =>
                    tab.classList.contains("active")
            );


        if (existingActive) {

            activateFinancialTab(
                existingActive.dataset.financialTab,
                false
            );

        } else {

            activateFinancialTab(
                tabs[0].dataset.financialTab,
                false
            );

        }

    }


    /* =====================================================
       EXPENSE CREATION MODAL
       ===================================================== */

    const expenseModal =
        $("#expenseModal");

    const openExpenseModal =
        $("#openExpenseModal");

    const closeExpenseModal =
        $("#closeExpenseModal");

    const cancelExpenseModal =
        $("#cancelExpenseModal");


    function closeNewExpenseModal() {

        expenseModal?.classList.remove(
            "active"
        );

    }


    openExpenseModal?.addEventListener(
        "click",
        function () {

            expenseModal?.classList.add(
                "active"
            );

        }
    );


    closeExpenseModal?.addEventListener(
        "click",
        closeNewExpenseModal
    );


    cancelExpenseModal?.addEventListener(
        "click",
        closeNewExpenseModal
    );


    expenseModal?.addEventListener(
        "click",
        function (event) {

            if (event.target === expenseModal) {
                closeNewExpenseModal();
            }

        }
    );


    /* =====================================================
       EXPENSE VIEW MODAL
       ===================================================== */

    const viewModal =
        $("#expenseViewModal");

    const closeViewModal =
        $("#closeExpenseViewModal");

    const viewExpenseNumber =
        $("#viewExpenseNumber");

    const viewExpenseDate =
        $("#viewExpenseDate");

    const viewExpenseCategory =
        $("#viewExpenseCategory");

    const viewExpensePaymentMethod =
        $("#viewExpensePaymentMethod");

    const viewExpenseReference =
        $("#viewExpenseReference");

    const viewExpenseDescription =
        $("#viewExpenseDescription");

    const viewExpenseNotes =
        $("#viewExpenseNotes");

    const viewExpenseCreatedBy =
        $("#viewExpenseCreatedBy");

    const viewExpenseCreatedAt =
        $("#viewExpenseCreatedAt");

    const viewExpenseAmount =
        $("#viewExpenseAmount");

    const viewExpenseStatus =
        $("#viewExpenseStatus");


    /*
     * Current expense being viewed.
     */

    let currentExpenseId = null;
    let currentExpenseNumber = null;


    /* =====================================================
       SHOW EXPENSE DETAILS
       ===================================================== */

    async function openExpense(expenseId) {

        if (!expenseId) {
            return;
        }


        currentExpenseId =
            expenseId;


        try {

            const response =
                await fetch(
                    `/financials/expenses/${expenseId}`,
                    {
                        method: "GET",
                        headers: {
                            "Accept":
                                "application/json"
                        }
                    }
                );


            const responseText =
                await response.text();


            if (!response.ok) {

                console.error(
                    "Expense response:",
                    responseText
                );

                throw new Error(
                    "Unable to load expense details."
                );

            }


            let expense;

            try {

                expense =
                    JSON.parse(
                        responseText
                    );

            } catch (jsonError) {

                console.error(
                    "Invalid JSON returned:",
                    responseText
                );

                throw new Error(
                    "The server returned an invalid response."
                );

            }


            /* -----------------------------------------
               BASIC DETAILS
               ----------------------------------------- */

            if (viewExpenseNumber) {
                viewExpenseNumber.textContent =
                    expense.expense_number ||
                    "Expense";
            }


            if (viewExpenseDate) {
                viewExpenseDate.textContent =
                    expense.expense_date ||
                    "—";
            }


            if (viewExpenseCategory) {
                viewExpenseCategory.textContent =
                    expense.category ||
                    "—";
            }


            if (viewExpensePaymentMethod) {
                viewExpensePaymentMethod.textContent =
                    expense.payment_method ||
                    "—";
            }


            if (viewExpenseReference) {
                viewExpenseReference.textContent =
                    expense.reference ||
                    "—";
            }


            if (viewExpenseDescription) {
                viewExpenseDescription.textContent =
                    expense.description ||
                    "—";
            }


            if (viewExpenseNotes) {
                viewExpenseNotes.textContent =
                    expense.notes ||
                    "—";
            }


            if (viewExpenseCreatedBy) {
                viewExpenseCreatedBy.textContent =
                    expense.created_by ||
                    "—";
            }


            if (viewExpenseCreatedAt) {
                viewExpenseCreatedAt.textContent =
                    expense.created_at ||
                    "—";
            }


            /* -----------------------------------------
               AMOUNT
               ----------------------------------------- */

            const amount =
                Number(
                    expense.amount || 0
                );


            if (viewExpenseAmount) {

                viewExpenseAmount.textContent =
                    `KES ${amount.toLocaleString(
                        "en-KE",
                        {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        }
                    )}`;

            }


            /* -----------------------------------------
               STATUS
               ----------------------------------------- */

            if (viewExpenseStatus) {

                const status =
                    expense.status ||
                    "—";


                viewExpenseStatus.textContent =
                    status;


                viewExpenseStatus.className =
                    "expense-status status-" +
                    String(status)
                        .toLowerCase()
                        .replace(/\s+/g, "-");

            }


            /* -----------------------------------------
               APPROVAL / REJECTION BUTTONS
               ----------------------------------------- */

            const approveBtn =
                $("#approveExpenseBtn");

            const rejectBtn =
                $("#rejectExpenseBtn");


            if (
                String(expense.status || "")
                    .toLowerCase() ===
                "pending"
            ) {

                if (approveBtn) {
                    approveBtn.style.display =
                        "inline-flex";
                }

                if (rejectBtn) {
                    rejectBtn.style.display =
                        "inline-flex";
                }

            } else {

                if (approveBtn) {
                    approveBtn.style.display =
                        "none";
                }

                if (rejectBtn) {
                    rejectBtn.style.display =
                        "none";
                }

            }


            /* -----------------------------------------
               SHOW MODAL
               ----------------------------------------- */

            viewModal?.classList.add(
                "active"
            );

        } catch (error) {

            console.error(
                "Error loading expense:",
                error
            );


            if (
                typeof showError ===
                "function"
            ) {

                showError(
                    error.message ||
                    "Unable to load expense details.",
                    "Unable to Load Expense"
                );

            } else if (
                typeof showNotification ===
                "function"
            ) {

                showNotification(
                    error.message ||
                    "Unable to load expense details.",
                    "error",
                    "Unable to Load Expense"
                );

            } else {

                alert(
                    error.message ||
                    "Unable to load expense details."
                );

            }

        }

    }


    /* =====================================================
       EXPENSE VIEW BUTTONS
       ===================================================== */

    /*
     * IMPORTANT:
     *
     * We use only buttons inside expense rows.
     * This prevents duplicate listeners and prevents
     * unrelated elements from being treated as expenses.
     */

    $$(
        "tbody tr[data-expense-id] [data-expense-id]"
    ).forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const expenseId =
                    this.dataset.expenseId;

                openExpense(
                    expenseId
                );

            }
        );

    });


    /* =====================================================
       CLOSE VIEW MODAL
       ===================================================== */

    closeViewModal?.addEventListener(
        "click",
        function () {

            viewModal?.classList.remove(
                "active"
            );

        }
    );


    viewModal?.addEventListener(
        "click",
        function (event) {

            if (event.target === viewModal) {

                viewModal.classList.remove(
                    "active"
                );

            }

        }
    );


    /* =====================================================
       APPROVE / REJECT ELEMENTS
       ===================================================== */

    const approveBtn =
        $("#approveExpenseBtn");

    const rejectBtn =
        $("#rejectExpenseBtn");

    const approveDialog =
        $("#approveExpenseDialog");

    const rejectDialog =
        $("#rejectExpenseDialog");

    const confirmApproveExpense =
        $("#confirmApproveExpense");

    const confirmRejectExpense =
        $("#confirmRejectExpense");

    const cancelApproveExpense =
        $("#cancelApproveExpense");

    const cancelRejectExpense =
        $("#cancelRejectExpense");

    const approveExpenseNumber =
        $("#approveExpenseNumber");

    const rejectExpenseNumber =
        $("#rejectExpenseNumber");

    const rejectionReason =
        $("#expenseRejectionReason");


    /* =====================================================
       APPROVE EXPENSE
       ===================================================== */

    approveBtn?.addEventListener(
        "click",
        function () {

            if (!currentExpenseId) {

                if (
                    typeof showError ===
                    "function"
                ) {

                    showError(
                        "No expense has been selected.",
                        "Approval Failed"
                    );

                }

                return;

            }


            currentExpenseNumber =
                viewExpenseNumber?.textContent ||
                "this expense";


            if (approveExpenseNumber) {

                approveExpenseNumber.textContent =
                    currentExpenseNumber;

            }


            approveDialog?.classList.add(
                "active"
            );

        }
    );


    /* =====================================================
       CANCEL APPROVAL
       ===================================================== */

    cancelApproveExpense?.addEventListener(
        "click",
        function () {

            approveDialog?.classList.remove(
                "active"
            );

        }
    );


    approveDialog?.addEventListener(
        "click",
        function (event) {

            if (event.target === approveDialog) {

                approveDialog.classList.remove(
                    "active"
                );

            }

        }
    );


    /* =====================================================
       CONFIRM APPROVAL
       ===================================================== */

    confirmApproveExpense?.addEventListener(
        "click",
        async function () {

            if (!currentExpenseId) {
                return;
            }


            confirmApproveExpense.disabled =
                true;


            try {

                const response =
                    await fetch(
                        `/financials/expenses/${currentExpenseId}/approve`,
                        {
                            method: "POST",
                            headers: {
                                "Accept":
                                    "application/json",
                                "Content-Type":
                                    "application/json"
                            }
                        }
                    );


                const responseText =
                    await response.text();


                /*
                 * Prevent the old:
                 *
                 * Unexpected token '<'
                 *
                 * problem when Flask returns HTML.
                 */

                if (!response.ok) {

                    console.error(
                        "Approval server response:",
                        responseText
                    );


                    let message =
                        "Unable to approve expense.";


                    try {

                        const errorData =
                            JSON.parse(
                                responseText
                            );

                        message =
                            errorData.message ||
                            message;

                    } catch (e) {

                        if (
                            responseText
                                .toLowerCase()
                                .includes("<!doctype")
                        ) {

                            message =
                                "The server returned an HTML page instead of an approval response.";

                        }

                    }


                    throw new Error(
                        message
                    );

                }


                let result;

                try {

                    result =
                        JSON.parse(
                            responseText
                        );

                } catch (e) {

                    console.error(
                        "Invalid approval JSON:",
                        responseText
                    );

                    throw new Error(
                        "The server returned an invalid approval response."
                    );

                }


                if (!result.success) {

                    throw new Error(
                        result.message ||
                        "Unable to approve expense."
                    );

                }


                /* -----------------------------------------
                   CLOSE DIALOGS
                   ----------------------------------------- */

                approveDialog?.classList.remove(
                    "active"
                );

                viewModal?.classList.remove(
                    "active"
                );


                /* -----------------------------------------
                   SAVE SUCCESS NOTIFICATION
                   ----------------------------------------- */

                sessionStorage.setItem(
                    "autovexNotification",
                    JSON.stringify({
                        type: "success",
                        title: "Expense Approved",
                        message:
                            result.message ||
                            "Expense approved successfully."
                    })
                );


                /* -----------------------------------------
                   RETURN TO EXPENSE TAB
                   ----------------------------------------- */

                window.location.href =
                    "/financials?tab=expenses";

            } catch (error) {

                console.error(
                    "Expense approval error:",
                    error
                );


                if (
                    typeof showError ===
                    "function"
                ) {

                    showError(
                        error.message ||
                        "Unable to approve expense.",
                        "Approval Failed"
                    );

                } else if (
                    typeof showNotification ===
                    "function"
                ) {

                    showNotification(
                        error.message ||
                        "Unable to approve expense.",
                        "error",
                        "Approval Failed"
                    );

                }

            } finally {

                confirmApproveExpense.disabled =
                    false;

            }

        }
    );


    /* =====================================================
       REJECT EXPENSE
       ===================================================== */

    rejectBtn?.addEventListener(
        "click",
        function () {

            if (!currentExpenseId) {

                if (
                    typeof showError ===
                    "function"
                ) {

                    showError(
                        "No expense has been selected.",
                        "Rejection Failed"
                    );

                }

                return;

            }


            currentExpenseNumber =
                viewExpenseNumber?.textContent ||
                "this expense";


            if (rejectExpenseNumber) {

                rejectExpenseNumber.textContent =
                    currentExpenseNumber;

            }


            if (rejectionReason) {

                rejectionReason.value = "";

                rejectionReason.classList.remove(
                    "error"
                );

            }


            viewModal?.classList.remove(
                "active"
            );


            rejectDialog?.classList.add(
                "active"
            );


            setTimeout(
                function () {

                    rejectionReason?.focus();

                },
                100
            );

        }
    );


    /* =====================================================
       CANCEL REJECTION
       ===================================================== */

    cancelRejectExpense?.addEventListener(
        "click",
        function () {

            rejectDialog?.classList.remove(
                "active"
            );

        }
    );


    rejectDialog?.addEventListener(
        "click",
        function (event) {

            if (event.target === rejectDialog) {

                rejectDialog.classList.remove(
                    "active"
                );

            }

        }
    );


    /* =====================================================
       CONFIRM REJECTION
       ===================================================== */

    confirmRejectExpense?.addEventListener(
        "click",
        async function () {

            if (!currentExpenseId) {
                return;
            }


            const reason =
                rejectionReason?.value
                    .trim() || "";


            /* -----------------------------------------
               VALIDATE REASON
               ----------------------------------------- */

            if (!reason) {

                rejectionReason?.classList.add(
                    "error"
                );


                if (
                    typeof showWarning ===
                    "function"
                ) {

                    showWarning(
                        "Please provide a reason for rejecting this expense.",
                        "Rejection Reason Required"
                    );

                } else if (
                    typeof showNotification ===
                    "function"
                ) {

                    showNotification(
                        "Please provide a reason for rejecting this expense.",
                        "warning",
                        "Rejection Reason Required"
                    );

                }


                rejectionReason?.focus();

                return;

            }


            rejectionReason?.classList.remove(
                "error"
            );


            confirmRejectExpense.disabled =
                true;


            try {

                const response =
                    await fetch(
                        `/financials/expenses/${currentExpenseId}/reject`,
                        {
                            method: "POST",
                            headers: {
                                "Accept":
                                    "application/json",
                                "Content-Type":
                                    "application/json"
                            },
                            body:
                                JSON.stringify({
                                    reason:
                                        reason
                                })
                        }
                    );


                const responseText =
                    await response.text();


                if (!response.ok) {

                    console.error(
                        "Rejection server response:",
                        responseText
                    );


                    let message =
                        "Unable to reject expense.";


                    try {

                        const errorData =
                            JSON.parse(
                                responseText
                            );

                        message =
                            errorData.message ||
                            message;

                    } catch (e) {

                        if (
                            responseText
                                .toLowerCase()
                                .includes("<!doctype")
                        ) {

                            message =
                                "The server returned an HTML page instead of a rejection response.";

                        }

                    }


                    throw new Error(
                        message
                    );

                }


                let result;

                try {

                    result =
                        JSON.parse(
                            responseText
                        );

                } catch (e) {

                    console.error(
                        "Invalid rejection JSON:",
                        responseText
                    );

                    throw new Error(
                        "The server returned an invalid rejection response."
                    );

                }


                if (!result.success) {

                    throw new Error(
                        result.message ||
                        "Unable to reject expense."
                    );

                }


                /* -----------------------------------------
                   CLOSE DIALOG
                   ----------------------------------------- */

                rejectDialog?.classList.remove(
                    "active"
                );


                /* -----------------------------------------
                   SAVE NOTIFICATION
                   ----------------------------------------- */

                sessionStorage.setItem(
                    "autovexNotification",
                    JSON.stringify({
                        type: "error",
                        title: "Expense Rejected",
                        message:
                            result.message ||
                            "Expense rejected successfully."
                    })
                );


                /* -----------------------------------------
                   RETURN TO EXPENSE TAB
                   ----------------------------------------- */

                window.location.href =
                    "/financials?tab=expenses";

            } catch (error) {

                console.error(
                    "Expense rejection error:",
                    error
                );


                if (
                    typeof showError ===
                    "function"
                ) {

                    showError(
                        error.message ||
                        "Unable to reject expense.",
                        "Rejection Failed"
                    );

                } else if (
                    typeof showNotification ===
                    "function"
                ) {

                    showNotification(
                        error.message ||
                        "Unable to reject expense.",
                        "error",
                        "Rejection Failed"
                    );

                }

            } finally {

                confirmRejectExpense.disabled =
                    false;

            }

        }
    );


    /* =====================================================
       EXPENSE FILTERS
       ===================================================== */

    const searchInput =
        $("#expenseSearch");

    const categorySelect =
        $("#expenseCategory");

    const statusSelect =
        $("#expenseStatus");

    const periodSelect =
        $("#expensePeriod");

    const clearFiltersBtn =
        $("#clearExpenseFilters");

    const filterCount =
        $("#expenseFilterCount");


    /*
     * Only actual expense table rows.
     */

    function getExpenseRows() {

        return Array.from(
            document.querySelectorAll(
                "tbody tr[data-expense-id]"
            )
        );

    }


    /* =====================================================
       DATE RANGE
       ===================================================== */

    function getPeriodRange(period) {

        const now =
            new Date();


        let start = null;
        let end = null;


        /* -----------------------------------------
           THIS MONTH
           ----------------------------------------- */

        if (period === "this_month") {

            start =
                new Date(
                    now.getFullYear(),
                    now.getMonth(),
                    1
                );


            end =
                new Date(
                    now.getFullYear(),
                    now.getMonth() + 1,
                    0,
                    23,
                    59,
                    59,
                    999
                );

        }


        /* -----------------------------------------
           LAST MONTH
           ----------------------------------------- */

        else if (period === "last_month") {

            start =
                new Date(
                    now.getFullYear(),
                    now.getMonth() - 1,
                    1
                );


            end =
                new Date(
                    now.getFullYear(),
                    now.getMonth(),
                    0,
                    23,
                    59,
                    59,
                    999
                );

        }


        /* -----------------------------------------
           THIS QUARTER
           ----------------------------------------- */

        else if (period === "this_quarter") {

            const quarterStartMonth =
                Math.floor(
                    now.getMonth() / 3
                ) * 3;


            start =
                new Date(
                    now.getFullYear(),
                    quarterStartMonth,
                    1
                );


            end =
                new Date(
                    now.getFullYear(),
                    quarterStartMonth + 3,
                    0,
                    23,
                    59,
                    59,
                    999
                );

        }


        /* -----------------------------------------
           THIS YEAR
           ----------------------------------------- */

        else if (period === "this_year") {

            start =
                new Date(
                    now.getFullYear(),
                    0,
                    1
                );


            end =
                new Date(
                    now.getFullYear(),
                    11,
                    31,
                    23,
                    59,
                    59,
                    999
                );

        }


        return {
            start: start,
            end: end
        };

    }


    /* =====================================================
       PARSE EXPENSE DATE
       ===================================================== */

    function parseExpenseDate(dateString) {

        if (!dateString) {
            return null;
        }


        const parts =
            dateString.split("-");


        if (parts.length !== 3) {
            return null;
        }


        /*
         * Construct locally rather than using
         * new Date("YYYY-MM-DD"), which can introduce
         * timezone-related date shifts.
         */

        return new Date(
            Number(parts[0]),
            Number(parts[1]) - 1,
            Number(parts[2])
        );

    }


    /* =====================================================
       FILTER EMPTY STATE
       ===================================================== */

    function updateEmptyState(
        visibleCount,
        rows
    ) {

        const tableBody =
            rows.length > 0
                ? rows[0].closest("tbody")
                : document.querySelector(
                    ".financial-table tbody"
                );


        if (!tableBody) {
            return;
        }


        let emptyRow =
            document.getElementById(
                "expenseFilterEmpty"
            );


        if (visibleCount === 0) {

            if (!emptyRow) {

                emptyRow =
                    document.createElement("tr");

                emptyRow.id =
                    "expenseFilterEmpty";


                emptyRow.innerHTML = `
                    <td colspan="8">

                        <div
                            class="expense-empty-state"
                        >

                            <i class="bx bx-search-alt"></i>

                            <p>
                                No expenses match your filters.
                            </p>

                        </div>

                    </td>
                `;


                tableBody.appendChild(
                    emptyRow
                );

            }


            emptyRow.style.display =
                "";

        } else {

            if (emptyRow) {

                emptyRow.style.display =
                    "none";

            }

        }

    }


    /* =====================================================
       FILTER RESULT COUNT
       ===================================================== */

    function updateFilterCount(
        visibleCount,
        totalCount
    ) {

        if (!filterCount) {
            return;
        }


        if (totalCount === 0) {

            filterCount.textContent =
                "No expenses";

            return;

        }


        if (visibleCount === totalCount) {

            if (totalCount === 1) {

                filterCount.textContent =
                    "Showing 1 expense";

            } else {

                filterCount.textContent =
                    `Showing ${totalCount} expenses`;

            }

            return;

        }


        if (visibleCount === 1) {

            filterCount.textContent =
                `Showing 1 of ${totalCount} expenses`;

        } else {

            filterCount.textContent =
                `Showing ${visibleCount} of ${totalCount} expenses`;

        }

    }


    /* =====================================================
       APPLY EXPENSE FILTERS
       ===================================================== */

    function applyExpenseFilters() {

        if (
            !searchInput ||
            !categorySelect ||
            !statusSelect ||
            !periodSelect
        ) {

            return;

        }


        const search =
            searchInput.value
                .trim()
                .toLowerCase();


        const category =
            categorySelect.value
                .trim()
                .toLowerCase();


        const status =
            statusSelect.value
                .trim()
                .toLowerCase();


        const period =
            periodSelect.value;


        const range =
            getPeriodRange(
                period
            );


        const rows =
            getExpenseRows();


        let visibleCount =
            0;


        rows.forEach(function (row) {

            const rowText =
                row.textContent
                    .toLowerCase();


            const rowCategory =
                (
                    row.dataset.category ||
                    ""
                )
                    .trim()
                    .toLowerCase();


            const rowStatus =
                (
                    row.dataset.status ||
                    ""
                )
                    .trim()
                    .toLowerCase();


            const expenseDate =
                parseExpenseDate(
                    row.dataset.expenseDate
                );


            /* -----------------------------------------
               SEARCH
               ----------------------------------------- */

            const matchesSearch =
                !search ||
                rowText.includes(search);


            /* -----------------------------------------
               CATEGORY
               ----------------------------------------- */

            const matchesCategory =
                !category ||
                rowCategory === category;


            /* -----------------------------------------
               STATUS
               ----------------------------------------- */

            const matchesStatus =
                !status ||
                rowStatus === status;


            /* -----------------------------------------
               PERIOD
               ----------------------------------------- */

            let matchesDate = true;


            if (
                period !== "all_time" &&
                range.start &&
                range.end
            ) {

                matchesDate =
                    expenseDate !== null &&
                    expenseDate >= range.start &&
                    expenseDate <= range.end;

            }


            /* -----------------------------------------
               FINAL RESULT
               ----------------------------------------- */

            const shouldShow =
                matchesSearch &&
                matchesCategory &&
                matchesStatus &&
                matchesDate;


            row.style.display =
                shouldShow
                    ? ""
                    : "none";


            if (shouldShow) {
                visibleCount++;
            }

        });


        updateFilterCount(
            visibleCount,
            rows.length
        );


        updateEmptyState(
            visibleCount,
            rows
        );

    }


    /* =====================================================
       FILTER EVENT LISTENERS
       ===================================================== */

    searchInput?.addEventListener(
        "input",
        applyExpenseFilters
    );


    categorySelect?.addEventListener(
        "change",
        applyExpenseFilters
    );


    statusSelect?.addEventListener(
        "change",
        applyExpenseFilters
    );


    periodSelect?.addEventListener(
        "change",
        applyExpenseFilters
    );


    /* =====================================================
       CLEAR FILTERS
       ===================================================== */

    clearFiltersBtn?.addEventListener(
        "click",
        function () {

            if (searchInput) {
                searchInput.value = "";
            }


            if (categorySelect) {
                categorySelect.value = "";
            }


            if (statusSelect) {
                statusSelect.value = "";
            }


            if (periodSelect) {
                periodSelect.value = "all_time";
            }


            applyExpenseFilters();

        }
    );


    /*
     * Apply filters immediately on page load.
     */

    if (
        searchInput &&
        categorySelect &&
        statusSelect &&
        periodSelect
    ) {

        applyExpenseFilters();

    }


    /* =====================================================
       RESTORE NOTIFICATION AFTER REDIRECT
       ===================================================== */

    const savedNotification =
        sessionStorage.getItem(
            "autovexNotification"
        );


    if (savedNotification) {

        /*
         * Remove immediately so a refresh doesn't
         * display the same notification twice.
         */

        sessionStorage.removeItem(
            "autovexNotification"
        );


        try {

            const notification =
                JSON.parse(
                    savedNotification
                );


            setTimeout(
                function () {

                    /*
                     * Prefer the existing global
                     * notification functions.
                     */

                    if (
                        typeof showNotification ===
                        "function"
                    ) {

                        showNotification(
                            notification.message ||
                            "Operation completed successfully.",
                            notification.type ||
                            "success",
                            notification.title ||
                            "Success"
                        );

                    } else if (
                        notification.type ===
                        "success" &&
                        typeof showSuccess ===
                        "function"
                    ) {

                        showSuccess(
                            notification.message,
                            notification.title ||
                            "Success"
                        );

                    } else if (
                        notification.type ===
                        "error" &&
                        typeof showError ===
                        "function"
                    ) {

                        showError(
                            notification.message,
                            notification.title ||
                            "Error"
                        );

                    } else if (
                        notification.type ===
                        "warning" &&
                        typeof showWarning ===
                        "function"
                    ) {

                        showWarning(
                            notification.message,
                            notification.title ||
                            "Warning"
                        );

                    } else {

                        /*
                         * No global notification
                         * system available.
                         *
                         * Do not use browser alert here.
                         * The notification CSS/JS should
                         * normally provide showNotification().
                         */

                        console.warn(
                            "Autovex notification system is not available."
                        );

                    }

                },
                250
            );


        } catch (error) {

            console.error(
                "Notification restore error:",
                error
            );

        }

    }


    /* =====================================================
       GLOBAL ESCAPE KEY
       ===================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (event.key !== "Escape") {
                return;
            }


            expenseModal?.classList.remove(
                "active"
            );


            viewModal?.classList.remove(
                "active"
            );


            approveDialog?.classList.remove(
                "active"
            );


            rejectDialog?.classList.remove(
                "active"
            );

        }
    );


});

// =====================================================
// DEBTOR FILTERS
// =====================================================

document.addEventListener("DOMContentLoaded", function () {

    const searchInput =
        document.getElementById("debtorSearch");

    const agingFilter =
        document.getElementById("debtorAging");

    const statusFilter =
        document.getElementById("debtorStatus");

    const periodFilter =
        document.getElementById("debtorPeriod");

    const viewAllButton =
        document.getElementById("viewAllDebtors");


    // =================================================
    // CHECK FILTER ELEMENTS
    // =================================================

    if (
        !searchInput ||
        !agingFilter ||
        !statusFilter ||
        !periodFilter
    ) {
        console.warn(
            "Debtor filter elements not found."
        );

        return;
    }


    // =================================================
    // FIND DEBTOR TABLE
    // =================================================

    const tables =
        document.querySelectorAll(
            ".financial-table"
        );

    let debtorTable = null;


    tables.forEach(function (table) {

        const headers =
            Array.from(
                table.querySelectorAll("thead th")
            ).map(function (header) {

                return header.textContent
                    .trim()
                    .toLowerCase();

            });


        if (
            headers.includes("customer") &&
            headers.includes("invoice") &&
            headers.includes("invoice date") &&
            headers.includes("due date") &&
            headers.includes("balance")
        ) {

            debtorTable = table;

        }

    });


    if (!debtorTable) {

        console.warn(
            "Debtor table not found."
        );

        return;

    }


    const tbody =
        debtorTable.querySelector("tbody");


    if (!tbody) {

        console.warn(
            "Debtor table body not found."
        );

        return;

    }


    const rows =
        Array.from(
            tbody.querySelectorAll("tr")
        );


    // =================================================
    // NORMALIZE TEXT
    // =================================================

    function normalize(value) {

        return String(value || "")
            .trim()
            .toLowerCase();

    }


    // =================================================
    // PARSE INVOICE DATE
    //
    // Example:
    // 12 Aug 2026
    // =================================================

    function parseDate(value) {

        const text =
            String(value || "")
                .trim()
                .replace(/\s+/g, " ");


        if (!text) {
            return null;
        }


        const parts =
            text.split(" ");


        if (parts.length !== 3) {
            return null;
        }


        const day =
            parseInt(parts[0], 10);


        const months = {
            jan: 0,
            feb: 1,
            mar: 2,
            apr: 3,
            may: 4,
            jun: 5,
            jul: 6,
            aug: 7,
            sep: 8,
            oct: 9,
            nov: 10,
            dec: 11
        };


        const month =
            months[
                parts[1].toLowerCase()
            ];


        const year =
            parseInt(parts[2], 10);


        if (
            isNaN(day) ||
            month === undefined ||
            isNaN(year)
        ) {

            return null;

        }


        return new Date(
            year,
            month,
            day
        );

    }


    // =================================================
    // PERIOD FILTER
    // =================================================

    function matchesPeriod(
        invoiceDate,
        selectedPeriod
    ) {

        if (
            !selectedPeriod ||
            selectedPeriod === "All Time"
        ) {
            return true;
        }


        if (!invoiceDate) {
            return false;
        }


        const today =
            new Date();


        const currentYear =
            today.getFullYear();

        const currentMonth =
            today.getMonth();


        // -------------------------------------------------
        // THIS MONTH
        // -------------------------------------------------

        if (
            selectedPeriod === "This Month"
        ) {

            return (
                invoiceDate.getFullYear() === currentYear &&
                invoiceDate.getMonth() === currentMonth
            );

        }


        // -------------------------------------------------
        // LAST MONTH
        // -------------------------------------------------

        if (
            selectedPeriod === "Last Month"
        ) {

            let month =
                currentMonth - 1;

            let year =
                currentYear;


            if (month < 0) {

                month = 11;
                year--;

            }


            return (
                invoiceDate.getFullYear() === year &&
                invoiceDate.getMonth() === month
            );

        }


        // -------------------------------------------------
        // THIS QUARTER
        // -------------------------------------------------

        if (
            selectedPeriod === "This Quarter"
        ) {

            const quarter =
                Math.floor(
                    currentMonth / 3
                );


            const quarterStart =
                quarter * 3;


            return (
                invoiceDate.getFullYear() === currentYear &&
                invoiceDate.getMonth() >= quarterStart &&
                invoiceDate.getMonth() <=
                    quarterStart + 2
            );

        }


        // -------------------------------------------------
        // THIS YEAR
        // -------------------------------------------------

        if (
            selectedPeriod === "This Year"
        ) {

            return (
                invoiceDate.getFullYear() === currentYear
            );

        }


        return true;

    }


    // =================================================
    // GET AGE IN DAYS
    // =================================================

    function getAgeDays(ageText) {

        const match =
            String(ageText || "")
                .match(/\d+/);


        if (!match) {
            return null;
        }


        return parseInt(
            match[0],
            10
        );

    }


    // =================================================
    // AGING FILTER
    // =================================================

    function matchesAging(
        ageText,
        selectedAging
    ) {

        if (!selectedAging) {
            return true;
        }


        const days =
            getAgeDays(ageText);


        if (days === null) {
            return false;
        }


        // -------------------------------------------------
        // CURRENT
        // 0–30 DAYS
        // -------------------------------------------------

        if (
            selectedAging === "current"
        ) {

            return (
                days >= 0 &&
                days <= 30
            );

        }


        // -------------------------------------------------
        // 31–60 DAYS
        // -------------------------------------------------

        if (
            selectedAging === "31–60 days"
        ) {

            return (
                days >= 31 &&
                days <= 60
            );

        }


        // -------------------------------------------------
        // 61–90 DAYS
        // -------------------------------------------------

        if (
            selectedAging === "61–90 days"
        ) {

            return (
                days >= 61 &&
                days <= 90
            );

        }


        // -------------------------------------------------
        // 90+ DAYS
        // -------------------------------------------------

        if (
            selectedAging === "90+ days"
        ) {

            return days > 90;

        }


        return true;

    }


    // =================================================
    // STATUS FILTER
    // =================================================

    function matchesStatus(
        statusText,
        selectedStatus
    ) {

        if (!selectedStatus) {
            return true;
        }


        // -------------------------------------------------
        // PARTIAL
        // -------------------------------------------------

        if (
            selectedStatus === "partial"
        ) {

            return statusText.includes(
                "partial"
            );

        }


        // -------------------------------------------------
        // OUTSTANDING
        // -------------------------------------------------

        if (
            selectedStatus === "outstanding"
        ) {

            return (
                statusText.includes("outstanding") ||
                statusText.includes("partial") ||
                statusText.includes("overdue")
            );

        }


        // -------------------------------------------------
        // OVERDUE
        // -------------------------------------------------

        if (
            selectedStatus === "overdue"
        ) {

            return statusText.includes(
                "overdue"
            );

        }


        return true;

    }


    // =================================================
    // APPLY FILTERS
    // =================================================

    function applyDebtorFilters() {

        const search =
            normalize(
                searchInput.value
            );


        const aging =
            normalize(
                agingFilter.value
            );


        const status =
            normalize(
                statusFilter.value
            );


        const period =
            periodFilter.value;


        rows.forEach(function (row) {

            const cells =
                row.querySelectorAll("td");


            // Ignore non-data rows

            if (cells.length < 10) {
                return;
            }


            // -------------------------------------------------
            // CUSTOMER
            // -------------------------------------------------

            const customer =
                normalize(
                    cells[0].textContent
                );


            // -------------------------------------------------
            // INVOICE
            // -------------------------------------------------

            const invoice =
                normalize(
                    cells[1].textContent
                );


            // -------------------------------------------------
            // SEARCH
            // -------------------------------------------------

            const searchMatches =
                !search ||
                customer.includes(search) ||
                invoice.includes(search);


            // -------------------------------------------------
            // INVOICE DATE
            // -------------------------------------------------

            const invoiceDate =
                parseDate(
                    cells[2].textContent
                );


            const periodMatches =
                matchesPeriod(
                    invoiceDate,
                    period
                );


            // -------------------------------------------------
            // AGE
            // -------------------------------------------------

            const ageText =
                normalize(
                    cells[7].textContent
                );


            const agingMatches =
                matchesAging(
                    ageText,
                    aging
                );


            // -------------------------------------------------
            // STATUS
            // -------------------------------------------------

            const statusText =
                normalize(
                    cells[8].textContent
                );


            const statusMatches =
                matchesStatus(
                    statusText,
                    status
                );


            // -------------------------------------------------
            // FINAL RESULT
            // -------------------------------------------------

            const shouldShow =
                searchMatches &&
                agingMatches &&
                statusMatches &&
                periodMatches;


            row.style.display =
                shouldShow ? "" : "none";

        });

    }


    // =================================================
    // SEARCH
    // =================================================

    searchInput.addEventListener(
        "input",
        applyDebtorFilters
    );


    // =================================================
    // AGING
    // =================================================

    agingFilter.addEventListener(
        "change",
        applyDebtorFilters
    );


    // =================================================
    // STATUS
    // =================================================

    statusFilter.addEventListener(
        "change",
        applyDebtorFilters
    );


    // =================================================
    // PERIOD
    // =================================================

    periodFilter.addEventListener(
        "change",
        applyDebtorFilters
    );


    // =================================================
    // VIEW ALL
    // RESET ALL FILTERS
    // =================================================

    viewAllButton?.addEventListener(
        "click",
        function () {

            searchInput.value = "";

            agingFilter.value = "";

            statusFilter.value = "";

            periodFilter.value = "All Time";


            // Show every debtor row

            rows.forEach(function (row) {

                const cells =
                    row.querySelectorAll("td");


                if (cells.length >= 10) {

                    row.style.display = "";

                }

            });

        }
    );


    // =================================================
    // INITIAL STATE
    // =================================================
    //
    // Do not filter database records on page load.
    // Simply make sure all rows are visible.
    //

    rows.forEach(function (row) {

        const cells =
            row.querySelectorAll("td");


        if (cells.length >= 10) {

            row.style.display = "";

        }

    });

});