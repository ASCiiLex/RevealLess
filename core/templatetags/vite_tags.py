import json
from functools import lru_cache

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

DEV_SERVER = 'http://localhost:5173'
MANIFEST_PATH = settings.BASE_DIR / 'static' / 'frontend' / 'dist' / '.vite' / 'manifest.json'
DIST_URL = f'{settings.STATIC_URL}frontend/dist/'

# Obligatorio cuando no se sirve el index.html de Vite (que lo inyecta solo):
# sin él, @vitejs/plugin-react lanza "can't detect preamble" al cargar cualquier .tsx.
PREAMBULO_DEV = f"""
<script type="module">
  import RefreshRuntime from "{DEV_SERVER}/@react-refresh"
  RefreshRuntime.injectIntoGlobalHook(window)
  window.$RefreshReg$ = () => {{}}
  window.$RefreshSig$ = () => (type) => type
  window.__vite_plugin_react_preamble_installed__ = true
</script>
"""


@lru_cache(maxsize=1)
def _manifest():
    """El manifest no cambia mientras corre el proceso: se lee una sola vez."""
    return json.loads(MANIFEST_PATH.read_text())


def _chunks_importados(manifest, nombre, vistos):
    """Chunks importados estáticamente, en orden de dependencia (primero los más profundos)."""
    for importado in manifest[nombre].get('imports', []):
        if importado not in vistos:
            vistos.add(importado)
            yield from _chunks_importados(manifest, importado, vistos)
            yield importado


@register.simple_tag
def vite_asset(entry='src/main.tsx'):
    """En DEBUG apunta al servidor de Vite (HMR). En producción enlaza el bundle del manifest
    con todo su CSS: el de los chunks compartidos que importa y el de la propia entrada."""
    if settings.DEBUG:
        return mark_safe(
            PREAMBULO_DEV
            + f'<script type="module" src="{DEV_SERVER}/@vite/client"></script>'
            + f'<script type="module" src="{DEV_SERVER}/{entry}"></script>'
        )

    if not MANIFEST_PATH.exists():
        return mark_safe('<!-- vite manifest no encontrado: ejecuta npm run build -->')

    manifest = _manifest()
    if entry not in manifest:
        return mark_safe('<!-- entrada no encontrada en el manifest de vite -->')

    importados = list(_chunks_importados(manifest, entry, set()))
    # CSS compartido antes que el de la entrada: mismo orden de cascada que en desarrollo.
    css = []
    for nombre in importados + [entry]:
        for archivo in manifest[nombre].get('css', []):
            if archivo not in css:
                css.append(archivo)

    tags = [f'<link rel="stylesheet" href="{DIST_URL}{archivo}">' for archivo in css]
    tags.append(f'<script type="module" src="{DIST_URL}{manifest[entry]["file"]}"></script>')
    # Descarga en paralelo los chunks que la entrada pediría en cascada.
    tags += [f'<link rel="modulepreload" href="{DIST_URL}{manifest[n]["file"]}">' for n in importados]
    return mark_safe(''.join(tags))