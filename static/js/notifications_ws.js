document.addEventListener("DOMContentLoaded", () => {

    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";

    let socket = null;

    function updateBadges(count) {
        const badges = document.querySelectorAll("[data-notif-badge]");

        badges.forEach(badge => {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = "inline-block";
            } else {
                badge.textContent = "0";
                badge.style.display = "none";
            }

            badge.classList.add("bump");
            setTimeout(() => badge.classList.remove("bump"), 200);
        });

        if (typeof updateToggleBadge === "function") {
            updateToggleBadge();
        }
    }

    function connect() {
        socket = new WebSocket(
            protocol + window.location.host + "/ws/notifications/"
        );

        socket.onmessage = (e) => {
            const data = JSON.parse(e.data);

            let badges = document.querySelectorAll("[data-notif-badge]");
            let current = 0;

            if (badges.length > 0) {
                current = parseInt(badges[0].textContent || "0");
            }

            const updated = current + 1;
            updateBadges(updated);

            // 🔥 insertar en lista en tiempo real
            const list = document.getElementById("notifications-list");

            if (list) {
                const item = document.createElement("div");
                item.innerHTML = `
                    <a href="${data.url}" style="text-decoration:none;color:inherit;">
                        <div class="notification-item">
                            <img src="${data.avatar}" class="notification-avatar">
                            <div class="notification-text">
                                <strong>@${data.actor}</strong> ${data.verb}
                                <div class="notification-time">Ahora</div>
                            </div>
                        </div>
                    </a>
                `;
                list.prepend(item);
            }
        };

        socket.onclose = () => {
            setTimeout(connect, 1000);
        };
    }

    connect();
});