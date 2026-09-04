document.addEventListener("DOMContentLoaded", () => {
    const reactionIcons = {
        like: "👍",
        love: "❤️",
        funny: "😂",
        wow: "😮",
        sad: "😢"
    };

    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const reactionsSocket = new WebSocket(
        protocol + window.location.host + "/ws/reactions/"
    );

    reactionsSocket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        const type = data.object_type;
        const id = data.id;
        const count = data.count;
        const counter = document.querySelector(`.reaction-count[data-type="${type}"][data-id="${id}"] .count`);
        if (counter) {
            counter.textContent = count;
        }
    };

    document.addEventListener("click", (e) => {
        const btn = e.target.closest(".react-btn");
        const menu = e.target.closest(".reaction-menu");

        if (btn) {
            const wrapper = btn.parentElement;
            const menuEl = wrapper.querySelector(".reaction-menu");
            closeAllReactionMenus();
            if (menuEl) menuEl.classList.toggle("show");
            return;
        }

        if (menu) return;

        closeAllReactionMenus();
    });

    function closeAllReactionMenus() {
        document.querySelectorAll(".reaction-menu.show").forEach(m => m.classList.remove("show"));
    }

    document.addEventListener("click", async (e) => {
        const opt = e.target.closest(".reaction-option");
        if (!opt) return;

        const type = opt.dataset.type;
        const id = opt.dataset.id;
        const reaction = opt.dataset.reaction;

        let url = "";
        let body = "";

        if (type === "post") {
            url = "/posts/react/";
            body = `post_id=${id}&reaction=${reaction}`;
        } else if (type === "comment") {
            url = `/comments/react/${id}/`;
            body = `reaction=${reaction}`;
        } else {
            return;
        }

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body
        });

        const data = await response.json();

        const btn = document.querySelector(`.react-btn[data-type="${type}"][data-id="${id}"]`);
        if (btn) {
            const icon = btn.querySelector(".reaction-icon");
            if (data.removed) {
                icon.innerHTML = `
                    <svg class="heart-icon" viewBox="0 0 24 24">
                        <path d="M12.1 8.64l-.1.1-.11-.1C9.14 6.09 5.6 6.7 3.6 9.05c-2.04 2.39-1.67 5.97.83 8.05L12 21l7.57-3.9c2.5-2.08 2.87-5.66.83-8.05-2-2.35-5.54-2.96-8.3-.41z"
                              fill="none" stroke="#e0245e" stroke-width="2"/>
                    </svg>
                `;
            } else {
                icon.textContent = reactionIcons[reaction];
            }
        }

        if (data.count !== undefined) {
            const countEl = document.querySelector(`.reaction-count[data-type="${type}"][data-id="${id}"] .count`);
            if (countEl) {
                countEl.textContent = data.count;
            }
        }

        closeAllReactionMenus();
    });

    document.addEventListener("click", async (e) => {
        const trigger = e.target.closest(".reaction-count");
        if (!trigger) return;

        const id = trigger.dataset.id;
        const type = trigger.dataset.type;

        const url = (type === "post")
            ? `/posts/reactions/${id}/`
            : `/comments/reactions/${id}/`;

        const response = await fetch(url);
        const data = await response.json();

        const modalBody = document.getElementById("likesModalBody");
        const totalsBar = document.getElementById("reactionTotals");

        renderReactionTotals(data.totals, totalsBar);

        function renderList(filter = null) {
            const filtered = filterUsersByReaction(data.users, filter);
            modalBody.innerHTML = "";

            if (filtered.length === 0) {
                modalBody.innerHTML = "<p>No hay reacciones.</p>";
                return;
            }

            filtered.forEach(user => {
                const row = document.createElement("div");
                row.classList.add("like-user-row");

                row.innerHTML = `
                    <img src="${user.avatar_url}" class="like-user-avatar">
                    <a href="${user.profile_url}" class="like-user-username">${user.username}</a>
                    <span class="reaction-icon-list">${reactionIcons[user.reaction]}</span>
                `;

                modalBody.appendChild(row);
            });
        }

        renderList();

        totalsBar.querySelectorAll(".reaction-total-item").forEach(item => {
            item.addEventListener("click", () => {
                totalsBar.querySelectorAll(".reaction-total-item").forEach(i => i.classList.remove("active"));
                item.classList.add("active");

                const filter = item.dataset.filter;
                renderList(filter);
            });
        });

        const modal = new bootstrap.Modal(document.getElementById("likesModal"));
        modal.show();
    });

    function renderReactionTotals(totals, container) {
        const order = ["like", "love", "funny", "wow", "sad"];
        const icons = {
            like: "👍",
            love: "❤️",
            funny: "😂",
            wow: "😮",
            sad: "😢"
        };

        container.innerHTML = "";

        order.forEach(type => {
            const count = totals[type] || 0;

            const item = document.createElement("div");
            item.className = "reaction-total-item";
            item.dataset.filter = type;

            item.innerHTML = `
                <span>${icons[type]}</span>
                <span>${count}</span>
            `;

            container.appendChild(item);
        });
    }

    function filterUsersByReaction(users, reactionType) {
        if (!reactionType) return users;
        return users.filter(u => u.reaction === reactionType);
    }
});

function getCSRFToken() {
    const name = "csrftoken=";
    const decoded = decodeURIComponent(document.cookie);
    const cookies = decoded.split(";");

    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name)) {
            return cookie.substring(name.length);
        }
    }
    return "";
}