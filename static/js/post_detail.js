const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

/* --- LIKE DINÁMICO CON ICONOS Y ANIMACIÓN --- */
function updateHeartIcon(button, liked) {
    if (liked) {
        button.innerHTML = `
            <svg class="heart-icon filled" viewBox="0 0 24 24">
                <path d="M12 21s-6.72-3.54-9.33-6.15C.88 12.06.5 8.48 2.54 6.09c2-2.35 5.54-2.96 8.3-.41l1.16 1.17 1.16-1.17c2.76-2.55 6.3-1.94 8.3.41 2.04 2.39 1.67 5.97-.83 8.05C18.72 17.46 12 21 12 21z"
                      fill="#e0245e"/>
            </svg>`;
    } else {
        button.innerHTML = `
            <svg class="heart-icon" viewBox="0 0 24 24">
                <path d="M12.1 8.64l-.1.1-.11-.1C9.14 6.09 5.6 6.7 3.6 9.05c-2.04 2.39-1.67 5.97.83 8.05L12 21l7.57-3.9c2.5-2.08 2.87-5.66.83-8.05-2-2.35-5.54-2.96-8.3-.41z"
                      fill="none" stroke="#e0245e" stroke-width="2"/>
            </svg>`;
    }
}

/* --- ENVIAR COMENTARIO O RESPUESTA --- */
function sendComment(form, isReply=false) {
    const formData = new FormData(form);

    fetch("/comments/add/", {
        method: "POST",
        headers: { 'X-CSRFToken': csrftoken },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) return;

        const commentsCountEl = document.getElementById('commentsCount');
        commentsCountEl.textContent = parseInt(commentsCountEl.textContent) + 1;

        const html = `
        <div class="comment" data-id="${data.id}">
            <div class="comment-header">${data.user}</div>
            <div>${data.text}</div>
            <div class="comment-meta">${data.created_at}</div>
            <div class="comment-actions">
                <button class="like-comment-btn" data-id="${data.id}">
                    <svg class="heart-icon" viewBox="0 0 24 24">
                        <path d="M12.1 8.64l-.1.1-.11-.1C9.14 6.09 5.6 6.7 3.6 9.05c-2.04 2.39-1.67 5.97.83 8.05L12 21l7.57-3.9c2.5-2.08 2.87-5.66.83-8.05-2-2.35-5.54-2.96-8.3-.41z"
                              fill="none" stroke="#e0245e" stroke-width="2"/>
                    </svg>
                </button>

                <button class="likes-list-trigger like-box ms-2" data-id="${data.id}">
                    <span class="likes-count">0</span> me gusta
                </button>
            </div>
        </div>`;

        if (!isReply) {
            document.getElementById('commentsList').insertAdjacentHTML('beforeend', html);
        } else {
            const parentId = form.dataset.parentId;
            const parentComment = document.querySelector(`.comment[data-id="${parentId}"] .comment-replies`);
            parentComment.insertAdjacentHTML('beforeend', html);
        }

        form.reset();
        if (isReply) form.classList.add('d-none');
    });
}

/* --- RENDERIZAR LISTA DE USUARIOS EN EL MODAL --- */
function renderLikesModal(users) {
    const body = document.getElementById("likesModalBody");

    if (!users || users.length === 0) {
        body.innerHTML = "<p>Nadie ha dado me gusta aún.</p>";
        return;
    }

    body.innerHTML = users.map(u => `
        <div class="like-user-row">
            <img class="like-user-avatar" src="${u.avatar_url || 'https://via.placeholder.com/32'}" alt="@${u.username}">
            <a href="${u.profile_url}" class="like-user-username">@${u.username}</a>
        </div>
    `).join("");
}

/* --- EVENTOS PRINCIPALES --- */
document.getElementById('commentsList').addEventListener('click', function(e) {

    /* RESPONDER */
    if (e.target.classList.contains('reply-btn')) {
        const id = e.target.dataset.id;
        const form = document.querySelector(`.reply-form[data-parent-id="${id}"]`);
        form.classList.toggle('d-none');
    }

    /* LIKE COMENTARIO */
    if (e.target.closest('.like-comment-btn')) {
        const button = e.target.closest('.like-comment-btn');
        const id = button.dataset.id;
        const commentEl = button.closest('.comment');
        const likesCountEl = commentEl.querySelector('.likes-count');

        const formData = new FormData();
        formData.append('comment_id', id);

        fetch("/comments/toggle-like/", {
            method: "POST",
            headers: { 'X-CSRFToken': csrftoken },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            likesCountEl.textContent = data.likes_count;
            updateHeartIcon(button, data.liked);
        });
    }

    /* ELIMINAR COMENTARIO */
    if (e.target.classList.contains('delete-comment')) {
        const id = e.target.dataset.id;

        if (!confirm("¿Eliminar este comentario?")) return;

        fetch(`/comments/delete/${id}/`, {
            method: "POST",
            headers: { 'X-CSRFToken': csrftoken }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.querySelector(`.comment[data-id="${id}"]`).remove();
            }
        });
    }

    /* LISTA DE USUARIOS QUE DIERON LIKE A COMENTARIO */
    const trigger = e.target.closest(".likes-list-trigger");
    if (trigger) {
        const id = trigger.dataset.id;

        fetch(`/comments/likes/${id}/`)
            .then(res => res.json())
            .then(data => {
                renderLikesModal(data.users);
                const modal = new bootstrap.Modal(document.getElementById("likesModal"));
                modal.show();
            });
    }
});

/* --- LIKE EN POST --- */
document.addEventListener('click', function(e) {
    const likePostBtn = e.target.closest('.like-post-btn');
    if (likePostBtn) {
        const postId = likePostBtn.dataset.id;
        const formData = new FormData();
        formData.append('post_id', postId);

        fetch("/posts/like/", {
            method: "POST",
            headers: { 'X-CSRFToken': csrftoken },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            const countEl = document.getElementById('postLikesCount');
            if (countEl) countEl.textContent = data.likes_count;
            updateHeartIcon(likePostBtn, data.liked);
        });
    }

    const postLikesTrigger = e.target.closest('.post-likes-trigger');
    if (postLikesTrigger) {
        const postId = postLikesTrigger.dataset.id;

        fetch(`/posts/likes/${postId}/`)
            .then(res => res.json())
            .then(data => {
                renderLikesModal(data.users);
                const modal = new bootstrap.Modal(document.getElementById("likesModal"));
                modal.show();
            });
    }
});

/* --- FORMULARIOS DE RESPUESTA --- */
document.querySelectorAll('.reply-form').forEach(form => {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        sendComment(form, true);
    });
});

/* --- FORMULARIO PRINCIPAL --- */
const mainForm = document.getElementById('mainCommentForm');
if (mainForm) {
    mainForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendComment(mainForm, false);
    });
}