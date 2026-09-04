const btn = document.getElementById("headerToggleBtn");
const nav = document.getElementById("topNav");

function updateToggleBadge() {
    const notif = document.querySelector('[data-notif-badge]');
    const msg = document.querySelector('[data-msg-badge]');
    const toggle = document.getElementById("toggle-badge");

    if (!toggle) return;

    const notifCount = notif ? parseInt(notif.textContent || "0") : 0;
    const msgCount = msg ? parseInt(msg.textContent || "0") : 0;

    const total = notifCount + msgCount;

    if (total > 0) {
        toggle.textContent = total;
        toggle.style.display = "inline-block";
    } else {
        toggle.style.display = "none";
    }
}

// Toggle menú
if (btn && nav) {
    btn.addEventListener("click", () => {
        nav.classList.toggle("show");

        // 🔥 recalcular tras abrir/cerrar
        setTimeout(updateToggleBadge, 50);
    });
}

// 🔥 actualizar al cargar
document.addEventListener("DOMContentLoaded", () => {
    updateToggleBadge();
});