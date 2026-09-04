document.addEventListener("DOMContentLoaded", () => {

    // -----------------------------
    // MOSTRAR FORMULARIO DE RESPUESTA
    // -----------------------------
    document.addEventListener("click", (e) => {
        const btn = e.target.closest(".reply-btn");
        if (!btn) return;

        const comment = btn.closest(".comment");
        const form = comment.querySelector(".reply-form");

        if (form) form.classList.toggle("d-none");
    });

    // -----------------------------
    // COMENTARIO PRINCIPAL
    // -----------------------------
    const mainForm = document.getElementById("mainCommentForm");

    if (mainForm) {
        mainForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const formData = new FormData(mainForm);

            const response = await fetch("/comments/add/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken()
                },
                body: formData
            });

            const data = await response.json();
            if (data.error) return;

            const list = document.getElementById("commentsList");

            if (list && !data.parent_id) {
                list.insertAdjacentHTML("beforeend", `
                    <div class="comment" data-id="${data.id}">
                        <div class="comment-header">
                            <a href="/perfil/${data.user}/">@${data.user}</a>
                        </div>
                        <div>${data.text}</div>
                        <div class="comment-meta">${data.created_at}</div>
                        <div class="comment-replies"></div>
                    </div>
                `);
            }

            mainForm.reset();
        });
    }

    // -----------------------------
    // RESPUESTAS (FIX DEFINITIVO)
    // -----------------------------
    document.addEventListener("submit", async (e) => {

        // 🔥 SOLO forms de reply
        if (!e.target.classList.contains("reply-form")) return;

        e.preventDefault();

        const form = e.target;
        const comment = form.closest(".comment");
        const repliesContainer = comment.querySelector(".comment-replies");

        const formData = new FormData(form);

        const response = await fetch("/comments/add/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken()
            },
            body: formData
        });

        const data = await response.json();
        if (data.error) return;

        // 🔥 inserción garantizada en el sitio correcto
        if (repliesContainer) {
            repliesContainer.insertAdjacentHTML("beforeend", `
                <div class="comment" data-id="${data.id}">
                    <div class="comment-header">
                        <a href="/perfil/${data.user}/">@${data.user}</a>
                    </div>
                    <div>${data.text}</div>
                    <div class="comment-meta">${data.created_at}</div>
                </div>
            `);
        }

        form.reset();
        form.classList.add("d-none");
    });

    // -----------------------------
    // BORRAR
    // -----------------------------
    document.addEventListener("click", async (e) => {
        const btn = e.target.closest(".delete-comment");
        if (!btn) return;

        if (!confirm("¿Eliminar este comentario?")) return;

        const commentId = btn.dataset.id;

        const response = await fetch(`/comments/delete/${commentId}/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/x-www-form-urlencoded"
            }
        });

        const data = await response.json();

        if (data.success) {
            document.querySelector(`.comment[data-id="${commentId}"]`)?.remove();
        }
    });

});


// -----------------------------
// CSRF
// -----------------------------
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