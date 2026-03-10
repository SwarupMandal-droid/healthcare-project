// =============================================
// LIFELINE CARE — PATIENT DASHBOARD JS
// =============================================

function getCsrfToken() {
    return document.cookie
        .split('; ')
        .find(r => r.startsWith('csrftoken='))
        ?.split('=')[1] || document.querySelector('meta[name="csrf-token"]')?.content;
}

const NOTIF_CSRF = getCsrfToken();

// ── Load notifications on page load ──
document.addEventListener('DOMContentLoaded', function () {
    loadNotifications();
    // Poll every 60 seconds for new notifications
    setInterval(loadNotifications, 60000);
});

// ── Toggle dropdown ──
function toggleNotifDropdown() {
    const dropdown = document.getElementById('notifDropdown');
    const isOpen   = dropdown.classList.contains('open');

    // Close all other dropdowns
    document.querySelectorAll('.notif-dropdown.open')
            .forEach(d => d.classList.remove('open'));

    if (!isOpen) {
        dropdown.classList.add('open');
        loadNotifications();
    }
}

// Close when clicking outside
document.addEventListener('click', function (e) {
    const wrap = document.getElementById('notifWrap');
    if (wrap && !wrap.contains(e.target)) {
        document.getElementById('notifDropdown')
                ?.classList.remove('open');
    }
});

// ── Fetch notifications from API ──
async function loadNotifications() {
    try {
        const res  = await fetch('/notifications/unread/');
        const data = await res.json();

        // Update badge
        const badge = document.getElementById('notifBadge');
        if (badge) {
            if (data.count > 0) {
                badge.textContent = data.count > 99 ? '99+' : data.count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }

        // Render notification list
        renderNotifications(data.notifications);

    } catch (err) {
        console.error('Failed to load notifications:', err);
    }
}

// ── Render notification items ──
function renderNotifications(notifications) {
    const list = document.getElementById('notifList');
    if (!list) return;

    if (!notifications || notifications.length === 0) {
        list.innerHTML = `
            <div style="text-align:center;padding:32px;
                        color:var(--gray-400)">
                <i class="fas fa-bell-slash"
                   style="font-size:1.8rem;margin-bottom:10px;
                          display:block;opacity:0.3"></i>
                <p style="font-size:0.85rem">No notifications yet</p>
            </div>`;
        return;
    }

    const categoryIcons = {
        appointment: { icon: 'fas fa-calendar-check', color: '#2563EB', bg: '#EFF6FF' },
        payment:     { icon: 'fas fa-rupee-sign',      color: '#059669', bg: '#D1FAE5' },
        health:      { icon: 'fas fa-heartbeat',       color: '#DC2626', bg: '#FEE2E2' },
        system:      { icon: 'fas fa-bell',            color: '#D97706', bg: '#FEF3C7' },
    };

    list.innerHTML = notifications.map(n => {
        const cat   = categoryIcons[n.category] ||
                      categoryIcons['system'];
        const unread = !n.is_read
            ? 'style="background:#F8FAFF"' : '';
        const dot    = !n.is_read
            ? '<span class="notif-unread-dot"></span>' : '';

        return `
        <div class="notif-item" ${unread}
             onclick="handleNotifClick(${n.id}, '${n.link}')">
            <div class="notif-icon-wrap"
                 style="background:${cat.bg}">
                <i class="${cat.icon}"
                   style="color:${cat.color}"></i>
            </div>
            <div class="notif-content">
                <div class="notif-title">
                    ${dot}${n.title}
                </div>
                <div class="notif-msg">${n.message}</div>
                <div class="notif-time">${n.time}</div>
            </div>
        </div>`;
    }).join('');
}

// ── Handle notification click ──
async function handleNotifClick(id, link) {
    // Mark as read
    await fetch(`/notifications/mark/${id}/`, {
        method:  'POST',
        headers: { 'X-CSRFToken': NOTIF_CSRF },
    });

    // Navigate to link
    if (link) window.location.href = link;
    else document.getElementById('notifDropdown')
                 .classList.remove('open');

    loadNotifications();
}

// ── Mark all as read ──
async function markAllRead() {
    await fetch('/notifications/mark-read/', {
        method:  'POST',
        headers: { 'X-CSRFToken': NOTIF_CSRF },
    });
    loadNotifications();
}

// ---- Sidebar Toggle (global) ----
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
    document.body.style.overflow = sidebar.classList.contains('open') ? 'hidden' : '';
}

// ---- Close Modal (global) ----
function closeModal(id) {
    document.getElementById(id).classList.remove('open');
    document.body.style.overflow = '';
}

// Close modal on overlay click
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('open');
        document.body.style.overflow = '';
    }
});