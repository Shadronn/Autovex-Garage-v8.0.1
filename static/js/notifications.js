/* =========================================================
   AUTOVEX FINANCIALS
   financials.js
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    "use strict";


    /* =====================================================
       HELPER: SHOW NOTIFICATION AFTER PAGE RELOAD
       ===================================================== */

    function showReloadNotification() {

        const stored =
            sessionStorage.getItem(
                "autovexNotification"
            );

        if (!stored) {
            return;
        }

        sessionStorage.removeItem(
            "autovexNotification"
        );

        try {

            const notification =
                JSON.parse(stored);

            if (
                typeof showNotification === "function"
            ) {

                setTimeout(() => {

                    showNotification(
                        notification.message,
                        notification.type || "success",
                        notification.title || "Success"
                    );

                }, 150);

            }

        } catch (error) {

            console.error(
                "Notification error:",
                error
            );

        }
    }

    showReloadNotification();


    /* =====================================================
       FINANCIAL TABS
       ===================================================== */

    const tabs =
        document.querySelectorAll(
            "[data-financial-tab]"
        );

    const contents =
        document.querySelectorAll(
            ".financial-module-tab"
        );


    tabs.forEach(function (tab) {

        tab.addEventListener(
            "click",
            function () {

                const target =
                    this.dataset.financialTab;


                tabs.forEach(function (item) {

                    item.classList.remove(
                        "active"
                    );

                });


                contents.forEach(function (content) {

                    content.classList.remove(
                        "active"
                    );

                });


                this.classList.add(
                    "active"
                );


                const selected =
                    document.getElementById(
                        target
                    );


                if (selected) {

                    selected.classList.add(
                        "active"
                    );

                }

            }
        );

    });


    /* =====================================================
       NEW EXPENSE MODAL
       ===================================================== */

    const openExpenseModal =
        document.getElementById(
            "openExpenseModal"
        );

    const closeExpenseModal =
        document.getElementById(
            "closeExpenseModal"
        );

    const cancelExpenseModal =
        document.getElementById(
            "cancelExpenseModal"
        );

    const expenseModal =
        document.getElementById(
            "expenseModal"
        );


    if (
        openExpenseModal &&
        expenseModal
    ) {

        openExpenseModal.addEventListener(
            "click",
            function () {

                expenseModal.classList.add(
                    "active"
                );

            }
        );

    }


    if (
        closeExpenseModal &&
        expenseModal
    ) {

        closeExpenseModal.addEventListener(
            "click",
            function () {

                expenseModal.classList.remove(
                    "active"
                );

            }
        );

    }


    if (
        cancelExpenseModal &&
        expenseModal
    ) {

        cancelExpenseModal.addEventListener(
            "click",
            function () {

                expenseModal.classList.remove(
                    "active"
                );

            }
        );

    }


    if (expenseModal) {

        expenseModal.addEventListener(
            "click",
            function (event) {

                if (
                    event.target === expenseModal
                ) {

                    expenseModal.classList.remove(
                        "active"
                    );

                }

            }
        );

    }


    /* =====================================================
       EXPENSE VIEW MODAL
       ===================================================== */

    const viewModal =
        document.getElementById(
            "expenseViewModal"
        );

    const closeViewModal =
        document.getElementById(
            "closeExpenseViewModal"
        );

    const approveBtn =
        document.getElementById(
            "approveExpenseBtn"
        );

    const rejectBtn =
        document.getElementById(
            "rejectExpenseBtn"
        );


    let currentExpenseId = null;
    let currentExpenseNumber = null;


    /* =====================================================
       APPROVE DIALOG
       ===================================================== */

    const approveDialog =
        document.getElementById(
            "approveExpenseDialog"
        );

    const approveExpenseNumber =
        document.getElementById(
            "approveExpenseNumber"
        );

    const cancelApproveExpense =
        document.getElementById(
            "cancelApproveExpense"
        );

    const confirmApproveExpense =
        document.getElementById(
            "confirmApproveExpense"
        );


    /* =====================================================
       REJECT DIALOG
       ===================================================== */

    const rejectDialog =
        document.getElementById(
            "rejectExpenseDialog"
        );

    const rejectExpenseNumber =
        document.getElementById(
            "rejectExpenseNumber"
        );

    const rejectionReason =
        document.getElementById(
            "expenseRejectionReason"
        );

    const cancelRejectExpense =
        document.getElementById(
            "cancelRejectExpense"
        );

    const confirmRejectExpense =
        document.getElementById(
            "confirmRejectExpense"
        );


    /* =====================================================
       OPEN DIALOG
       ===================================================== */

    function openDialog(dialog) {

        if (!dialog) {
            return;
        }

        dialog.classList.add(
            "active"
        );

        dialog.setAttribute(
            "aria-hidden",
            "false"
        );

    }


    /* =====================================================
       CLOSE DIALOG
       ===================================================== */

    function closeDialog(dialog) {

        if (!dialog) {
            return;
        }

        dialog.classList.remove(
            "active"
        );

        dialog.setAttribute(
            "aria-hidden",
            "true"
        );

    }


    /* =====================================================
       CLOSE ALL DIALOGS
       ===================================================== */

    function closeAllDialogs() {

        closeDialog(
            approveDialog
        );

        closeDialog(
            rejectDialog
        );

    }


    /* =====================================================
       OPEN EXPENSE
       ===================================================== */

    async function openExpense(
        expenseId
    ) {

        if (!expenseId) {
            return;
        }


        currentExpenseId =
            expenseId;


        try {

            const response =
                await fetch(
                    `/financials/expenses/${expenseId}`
                );


            if (!response.ok) {

                throw new Error(
                    "Unable to load expense details."
                );

            }


            const expense =
                await response.json();


            currentExpenseNumber =
                expense.expense_number;


            const number =
                document.getElementById(
                    "viewExpenseNumber"
                );

            const date =
                document.getElementById(
                    "viewExpenseDate"
                );

            const category =
                document.getElementById(
                    "viewExpenseCategory"
                );

            const paymentMethod =
                document.getElementById(
                    "viewExpensePaymentMethod"
                );

            const reference =
                document.getElementById(
                    "viewExpenseReference"
                );

            const description =
                document.getElementById(
                    "viewExpenseDescription"
                );

            const notes =
                document.getElementById(
                    "viewExpenseNotes"
                );

            const createdBy =
                document.getElementById(
                    "viewExpenseCreatedBy"
                );

            const createdAt =
                document.getElementById(
                    "viewExpenseCreatedAt"
                );

            const amountElement =
                document.getElementById(
                    "viewExpenseAmount"
                );

            const statusElement =
                document.getElementById(
                    "viewExpenseStatus"
                );


            if (number) {

                number.textContent =
                    expense.expense_number ||
                    "Expense";

            }


            if (date) {

                date.textContent =
                    expense.expense_date ||
                    "—";

            }


            if (category) {

                category.textContent =
                    expense.category ||
                    "—";

            }


            if (paymentMethod) {

                paymentMethod.textContent =
                    expense.payment_method ||
                    "—";

            }


            if (reference) {

                reference.textContent =
                    expense.reference ||
                    "—";

            }


            if (description) {

                description.textContent =
                    expense.description ||
                    "—";

            }


            if (notes) {

                notes.textContent =
                    expense.notes ||
                    "—";

            }


            if (createdBy) {

                createdBy.textContent =
                    expense.created_by ||
                    "—";

            }


            if (createdAt) {

                createdAt.textContent =
                    expense.created_at ||
                    "—";

            }


            if (amountElement) {

                const amount =
                    Number(
                        expense.amount || 0
                    );


                amountElement.textContent =
                    `KES ${amount.toLocaleString(
                        "en-KE",
                        {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        }
                    )}`;

            }


            if (statusElement) {

                statusElement.textContent =
                    expense.status ||
                    "—";


                statusElement.className =
                    "expense-status status-" +
                    String(
                        expense.status || ""
                    )
                        .toLowerCase()
                        .replace(
                            /\s+/g,
                            "-"
                        );

            }


            /*
             * Approval buttons should only
             * appear for Pending expenses.
             */

            if (
                approveBtn &&
                rejectBtn
            ) {

                if (
                    expense.status ===
                    "Pending"
                ) {

                    approveBtn.style.display =
                        "inline-flex";

                    rejectBtn.style.display =
                        "inline-flex";

                } else {

                    approveBtn.style.display =
                        "none";

                    rejectBtn.style.display =
                        "none";

                }

            }


            if (viewModal) {

                viewModal.classList.add(
                    "active"
                );

            }

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

            }

        }

    }


    /* =====================================================
       VIEW BUTTONS
       ===================================================== */

    document
        .querySelectorAll(
            "[data-expense-id]"
        )
        .forEach(function (button) {

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
       APPROVE BUTTON
       ===================================================== */

    if (approveBtn) {

        approveBtn.addEventListener(
            "click",
            function () {

                if (
                    !currentExpenseId
                ) {

                    return;

                }


                if (approveExpenseNumber) {

                    approveExpenseNumber.textContent =
                        currentExpenseNumber ||
                        "this expense";

                }


                openDialog(
                    approveDialog
                );

            }
        );

    }


    /* =====================================================
       CANCEL APPROVAL
       ===================================================== */

    if (cancelApproveExpense) {

        cancelApproveExpense.addEventListener(
            "click",
            function () {

                closeDialog(
                    approveDialog
                );

            }
        );

    }


    /* =====================================================
       CONFIRM APPROVAL
       ===================================================== */

    if (confirmApproveExpense) {

        confirmApproveExpense.addEventListener(
            "click",
            async function () {

                if (
                    !currentExpenseId
                ) {

                    return;

                }


                try {

                    confirmApproveExpense.disabled =
                        true;


                    const response =
                        await fetch(
                            `/financials/expenses/${currentExpenseId}/approve`,
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type":
                                        "application/json"
                                }
                            }
                        );


                    const text =
                        await response.text();


                    let result;


                    try {

                        result =
                            JSON.parse(text);

                    } catch (parseError) {

                        console.error(
                            "Approval returned non-JSON:",
                            text
                        );

                        throw new Error(
                            `Server returned an unexpected response (${response.status}).`
                        );

                    }


                    if (
                        !response.ok ||
                        !result.success
                    ) {

                        throw new Error(
                            result.message ||
                            "Unable to approve expense."
                        );

                    }


                    closeDialog(
                        approveDialog
                    );


                    if (viewModal) {

                        viewModal.classList.remove(
                            "active"
                        );

                    }


                    /*
                     * Store notification so it
                     * survives the page reload.
                     */

                    sessionStorage.setItem(
                        "autovexNotification",
                        JSON.stringify({
                            type: "success",
                            title:
                                "Expense Approved",
                            message:
                                result.message ||
                                "Expense approved successfully."
                        })
                    );


                    window.location.reload();


                } catch (error) {

                    console.error(
                        "Approval error:",
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

                    }

                } finally {

                    confirmApproveExpense.disabled =
                        false;

                }

            }
        );

    }


    /* =====================================================
       REJECT BUTTON
       ===================================================== */

    if (rejectBtn) {

        rejectBtn.addEventListener(
            "click",
            function () {

                if (
                    !currentExpenseId
                ) {

                    return;

                }


                if (rejectExpenseNumber) {

                    rejectExpenseNumber.textContent =
                        currentExpenseNumber ||
                        "this expense";

                }


                if (rejectionReason) {

                    rejectionReason.value = "";

                    rejectionReason.classList.remove(
                        "error"
                    );

                }


                openDialog(
                    rejectDialog
                );


                setTimeout(
                    function () {

                        if (rejectionReason) {

                            rejectionReason.focus();

                        }

                    },
                    150
                );

            }
        );

    }


    /* =====================================================
       CANCEL REJECTION
       ===================================================== */

    if (cancelRejectExpense) {

        cancelRejectExpense.addEventListener(
            "click",
            function () {

                closeDialog(
                    rejectDialog
                );

            }
        );

    }


    /* =====================================================
       CONFIRM REJECTION
       ===================================================== */

    if (confirmRejectExpense) {

        confirmRejectExpense.addEventListener(
            "click",
            async function () {

                if (
                    !currentExpenseId
                ) {

                    return;

                }


                const reason =
                    rejectionReason
                        ? rejectionReason.value.trim()
                        : "";


                if (!reason) {

                    if (rejectionReason) {

                        rejectionReason.classList.add(
                            "error"
                        );

                        rejectionReason.focus();

                    }


                    if (
                        typeof showWarning ===
                        "function"
                    ) {

                        showWarning(
                            "A rejection reason is required.",
                            "Reason Required"
                        );

                    }

                    return;

                }


                if (rejectionReason) {

                    rejectionReason.classList.remove(
                        "error"
                    );

                }


                try {

                    confirmRejectExpense.disabled =
                        true;


                    const response =
                        await fetch(
                            `/financials/expenses/${currentExpenseId}/reject`,
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },
                                body:
                                    JSON.stringify({
                                        reason: reason
                                    })
                            }
                        );


                    const text =
                        await response.text();


                    let result;


                    try {

                        result =
                            JSON.parse(text);

                    } catch (parseError) {

                        console.error(
                            "Rejection returned non-JSON:",
                            text
                        );

                        throw new Error(
                            `Server returned an unexpected response (${response.status}).`
                        );

                    }


                    if (
                        !response.ok ||
                        !result.success
                    ) {

                        throw new Error(
                            result.message ||
                            "Unable to reject expense."
                        );

                    }


                    closeDialog(
                        rejectDialog
                    );


                    if (viewModal) {

                        viewModal.classList.remove(
                            "active"
                        );

                    }


                    sessionStorage.setItem(
                        "autovexNotification",
                        JSON.stringify({
                            type: "success",
                            title:
                                "Expense Rejected",
                            message:
                                result.message ||
                                "Expense rejected successfully."
                        })
                    );


                    window.location.reload();


                } catch (error) {

                    console.error(
                        "Rejection error:",
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

                    }

                } finally {

                    confirmRejectExpense.disabled =
                        false;

                }

            }
        );

    }


    /* =====================================================
       CLOSE VIEW MODAL
       ===================================================== */

    if (closeViewModal) {

        closeViewModal.addEventListener(
            "click",
            function () {

                if (viewModal) {

                    viewModal.classList.remove(
                        "active"
                    );

                }

            }
        );

    }


    /* =====================================================
       CLICK OUTSIDE VIEW MODAL
       ===================================================== */

    if (viewModal) {

        viewModal.addEventListener(
            "click",
            function (event) {

                if (
                    event.target === viewModal
                ) {

                    viewModal.classList.remove(
                        "active"
                    );

                }

            }
        );

    }


    /* =====================================================
       CLICK OUTSIDE DIALOGS
       ===================================================== */

    if (approveDialog) {

        approveDialog.addEventListener(
            "click",
            function (event) {

                if (
                    event.target ===
                    approveDialog
                ) {

                    closeDialog(
                        approveDialog
                    );

                }

            }
        );

    }


    if (rejectDialog) {

        rejectDialog.addEventListener(
            "click",
            function (event) {

                if (
                    event.target ===
                    rejectDialog
                ) {

                    closeDialog(
                        rejectDialog
                    );

                }

            }
        );

    }


    /* =====================================================
       ESCAPE KEY
       ===================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key !==
                "Escape"
            ) {

                return;

            }


            closeAllDialogs();


            if (viewModal) {

                viewModal.classList.remove(
                    "active"
                );

            }

        }
    );


    /* =====================================================
       REMOVE ERROR STATE WHEN TYPING
       ===================================================== */

    if (rejectionReason) {

        rejectionReason.addEventListener(
            "input",
            function () {

                if (
                    this.value.trim()
                ) {

                    this.classList.remove(
                        "error"
                    );

                }

            }
        );

    }

});