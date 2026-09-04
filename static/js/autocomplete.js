document.addEventListener('DOMContentLoaded', () => {

    const apiMentions = '/posts/mentions-search/';
    const apiHashtags = '/posts/hashtags-search/';
    const apiSuggested = '/posts/suggested-hashtags/';

    function createDropdown() {
        const box = document.createElement('div');
        box.className = 'autocomplete-dropdown';
        Object.assign(box.style, {
            position: 'absolute',
            zIndex: '9999',
            background: '#fff',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '0.9rem',
            maxHeight: '200px',
            overflowY: 'auto',
            display: 'none'
        });
        document.body.appendChild(box);
        return box;
    }

    const dropdown = createDropdown();
    let activeTextarea = null;

    function positionDropdown(textarea) {
        const rect = textarea.getBoundingClientRect();
        dropdown.style.left = rect.left + window.scrollX + 'px';
        dropdown.style.top = rect.bottom + window.scrollY + 'px';
        dropdown.style.minWidth = rect.width + 'px';
    }

    function closeDropdown() {
        dropdown.style.display = 'none';
        dropdown.innerHTML = '';
        activeTextarea = null;
    }

    function insertToken(textarea, token) {
        const start = textarea.selectionStart;
        const value = textarea.value;

        const before = value.slice(0, start);
        const after = value.slice(start);

        // 🔥 busca SOLO el hashtag en curso (al final del cursor)
        const match = before.match(/(#\w*)$/);

        if (match) {
            // reemplaza SOLO ese hashtag
            const newBefore = before.slice(0, -match[0].length) + token + ' ';
            textarea.value = newBefore + after;

            const pos = newBefore.length;
            textarea.setSelectionRange(pos, pos);
        } else {
            // inserta sin romper nada
            const newValue = before + token + ' ' + after;
            textarea.value = newValue;

            const pos = before.length + token.length + 1;
            textarea.setSelectionRange(pos, pos);
        }

        textarea.focus();
    }

    function renderResults(items, type) {
        if (!items.length) {
            closeDropdown();
            return;
        }

        dropdown.innerHTML = '';

        items.forEach(item => {
            const el = document.createElement('div');
            el.style.padding = '6px 10px';
            el.style.cursor = 'pointer';

            el.textContent = type === 'mention'
                ? '@' + item.username
                : '#' + item.name;

            el.addEventListener('mousedown', e => {
                e.preventDefault();
                if (activeTextarea) {
                    insertToken(activeTextarea, el.textContent);
                }
                closeDropdown();
            });

            dropdown.appendChild(el);
        });

        dropdown.style.display = 'block';
    }

    async function fetchResults(query, type) {
        const url = type === 'mention' ? apiMentions : apiHashtags;
        const params = new URLSearchParams({ q: query });

        const res = await fetch(url + '?' + params.toString());
        if (!res.ok) return [];

        const data = await res.json();
        return data.results || [];
    }

    function handleInput(e) {
        const textarea = e.target;
        if (!(textarea.tagName === 'TEXTAREA')) return;

        activeTextarea = textarea;
        positionDropdown(textarea);

        const value = textarea.value;
        const cursor = textarea.selectionStart;
        const before = value.slice(0, cursor);

        const lastAt = before.lastIndexOf('@');
        const lastHash = before.lastIndexOf('#');
        const triggerPos = Math.max(lastAt, lastHash);

        if (triggerPos === -1) {
            closeDropdown();
            return;
        }

        const triggerChar = before[triggerPos];
        const query = before.slice(triggerPos + 1).split(/\s/)[0];

        if (!query.length) {
            closeDropdown();
            return;
        }

        const type = triggerChar === '@' ? 'mention' : 'hashtag';

        fetchResults(query, type).then(items => {
            if (activeTextarea !== textarea) return;
            renderResults(items, type);
        });
    }

    document.addEventListener('input', handleInput);

    document.addEventListener('click', e => {
        if (!dropdown.contains(e.target)) {
            closeDropdown();
        }
    });

    // 🔥 HASHTAGS SUGERIDOS (CORREGIDO)
    async function loadSuggestedHashtags() {
        const box = document.getElementById('suggestedHashtags');
        if (!box) return;

        const res = await fetch(apiSuggested);
        if (!res.ok) return;

        const data = await res.json();
        const tags = data.results || [];

        box.innerHTML = '';

        tags.forEach(tag => {

            // 🔥 CAMBIO CLAVE → NO BUTTON
            const el = document.createElement('span');
            el.className = 'btn btn-sm btn-outline-secondary me-2 mb-2';
            el.style.cursor = 'pointer';
            el.textContent = '#' + tag;

            el.addEventListener('click', (e) => {
                e.preventDefault();

                const textarea = document.querySelector('textarea');
                if (!textarea) return;

                insertToken(textarea, '#' + tag);
            });

            box.appendChild(el);
        });
    }

    loadSuggestedHashtags();

});