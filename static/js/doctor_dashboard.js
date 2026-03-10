// =============================================
// LIFELINE CARE — DOCTOR DASHBOARD JS
// =============================================

document.addEventListener('DOMContentLoaded', function () {

    // ---- Notification Dropdown ----
    const notifBtn      = document.getElementById('notifBtn');
    const notifDropdown = document.getElementById('notifDropdown');

    if (notifBtn) {
        notifBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            notifDropdown.classList.toggle('open');
        });

        document.addEventListener('click', function () {
            notifDropdown.classList.remove('open');
        });

        notifDropdown.addEventListener('click', e => e.stopPropagation());
    }

});