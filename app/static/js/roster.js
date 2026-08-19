/**
 * SOC Shift Roster System Client-Side Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss Flash Alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

/**
 * Populates the Manual Shift Override Modal with target analyst details
 * @param {number} userId - Database ID of the analyst
 * @param {string} userName - Full name of the analyst
 * @param {string} date - Targeted date string (YYYY-MM-DD)
 * @param {string} currentShift - Active assigned shift code
 */
function setOverrideData(userId, userName, date, currentShift) {
    const userIdInput = document.getElementById('modal_user_id');
    const userNameInput = document.getElementById('modal_user_name');
    const dateInput = document.getElementById('modal_date');
    const shiftSelect = document.getElementById('modal_shift_type');

    if (userIdInput) userIdInput.value = userId;
    if (userNameInput) userNameInput.value = userName;
    if (dateInput) dateInput.value = date;
    if (shiftSelect) shiftSelect.value = currentShift;
}

/**
 * Validates that end date cannot be earlier than start date on Leave forms
 */
function validateLeaveDates() {
    const startDateInput = document.querySelector('input[name="start_date"]');
    const endDateInput = document.querySelector('input[name="end_date"]');

    if (startDateInput && endDateInput) {
        endDateInput.addEventListener('change', () => {
            if (startDateInput.value && endDateInput.value < startDateInput.value) {
                alert('End date cannot be earlier than start date.');
                endDateInput.value = startDateInput.value;
            }
        });
    }
}

// Initialize date validation
validateLeaveDates();