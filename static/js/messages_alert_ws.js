document.addEventListener("DOMContentLoaded", () => {

    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";

    let socket = null;

    function updateBadges(count) {
        const badges = document.querySelectorAll("[data-msg-badge]");

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
            protocol + window.location.host + "/ws/messages/"
        );

        socket.onmessage = (e) => {
            const data = JSON.parse(e.data);

            let badges = document.querySelectorAll("[data-msg-badge]");
            let current = 0;

            if (badges.length > 0) {
                current = parseInt(badges[0].textContent || "0");
            }

            if (data.type === "new_message") {
                const updated = current + (data.count || 1);
                updateBadges(updated);
            }

            if (data.type === "reset") {
                updateBadges(0);
            }
        };

        socket.onclose = () => {
            setTimeout(connect, 1000);
        };
    }

    connect();
});