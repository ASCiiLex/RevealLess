document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("globalSearchInput");
    const resultsBox = document.getElementById("globalSearchResults");

    if (!input || !resultsBox) return;

    let timeout = null;

    input.addEventListener("input", () => {
        const query = input.value.trim();

        if (timeout) clearTimeout(timeout);

        if (query.length === 0) {
            resultsBox.innerHTML = "";
            resultsBox.style.display = "none";
            return;
        }

        timeout = setTimeout(() => {
            fetch(`/posts/search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    renderResults(data);
                })
                .catch(err => {
                    console.error("Error en búsqueda global:", err);
                });
        }, 300);
    });

    function renderResults(data) {
        resultsBox.innerHTML = "";

        const hasUsers = data.users && data.users.length > 0;
        const hasPosts = data.posts && data.posts.length > 0;
        const hasHashtags = data.hashtags && data.hashtags.length > 0;

        if (!hasUsers && !hasPosts && !hasHashtags) {
            resultsBox.innerHTML = `<div class="p-2 text-muted">Sin resultados</div>`;
            resultsBox.style.display = "block";
            return;
        }

        let html = "";

        if (hasUsers) {
            html += `<div class="px-2 py-1 fw-bold text-primary">Usuarios</div>`;
            data.users.forEach(user => {
                const img = user.image || "/static/img/default_profile.jpg";
                html += `
                    <a href="/perfil/${user.username}/" class="search-item">
                        <img src="${img}" class="search-avatar">
                        <span>${user.username}</span>
                    </a>
                `;
            });
        }

        if (hasHashtags) {
            html += `<div class="px-2 py-1 fw-bold text-success mt-2">Hashtags</div>`;
            data.hashtags.forEach(tag => {
                html += `
                    <a href="/posts/hashtag/${tag.name}/" class="search-item">
                        <span>#${tag.name}</span>
                    </a>
                `;
            });
        }

        if (hasPosts) {
            html += `<div class="px-2 py-1 fw-bold text-primary mt-2">Posts</div>`;
            data.posts.forEach(post => {
                const img = post.image || "/static/img/default_post.jpg";
                html += `
                    <a href="/posts/${post.id}/" class="search-item">
                        <img src="${img}" class="search-thumb">
                        <span>${post.text}</span>
                    </a>
                `;
            });
        }

        resultsBox.innerHTML = html;
        resultsBox.style.display = "block";
    }

    document.addEventListener("click", (e) => {
        if (!resultsBox.contains(e.target) && e.target !== input) {
            resultsBox.style.display = "none";
        }
    });
});