import json
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

DEV_SERVER = 'http://localhost:5173'
MANIFEST_PATH = settings.BASE_DIR / 'static' / 'frontend' / 'dist' / '.vite' / 'manifest.json'


@register.simple_tag
def vite_asset(entry='src/main.tsx'):
    """En DEBUG, apunta al servidor de Vite en modo watch (HMR).
    En producción, lee dist/.vite/manifest.json (generado por `npm run
    build`) y sirve el bundle final vía WhiteNoise, igual que el resto
    de static/."""
    if settings.DEBUG:
        # El preámbulo de React Refresh es obligatorio cuando no se sirve
        # el index.html de Vite (que lo inyecta automáticamente): sin
        # esto, @vitejs/plugin-react lanza "can't detect preamble" en
        # cuanto se carga cualquier módulo .tsx.
        preamble = f"""
        <script type="module">
          import RefreshRuntime from "{DEV_SERVER}/@react-refresh"
          RefreshRuntime.injectIntoGlobalHook(window)
          window.$RefreshReg$ = () => {{}}
          window.$RefreshSig$ = () => (type) => type
          window.__vite_plugin_react_preamble_installed__ = true
        </script>
        """
        return mark_safe(
            preamble
            + f'<script type="module" src="{DEV_SERVER}/@vite/client"></script>'
            + f'<script type="module" src="{DEV_SERVER}/{entry}"></script>'
        )

    if not MANIFEST_PATH.exists():
        return mark_safe('<!-- vite manifest no encontrado: ejecuta npm run build -->')

    manifest = json.loads(MANIFEST_PATH.read_text())
    chunk = manifest.get(entry)
    if not chunk:
        return mark_safe('<!-- entrada no encontrada en el manifest de vite -->')

    tags = [f'<script type="module" src="/static/frontend/dist/{chunk["file"]}"></script>']
    for css_file in chunk.get('css', []):
        tags.append(f'<link rel="stylesheet" href="/static/frontend/dist/{css_file}">')

    return mark_safe(''.join(tags))