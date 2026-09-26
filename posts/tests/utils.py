from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from posts.models import Post


def crear_obra(slug, n=1, tipo_unidad='episodio', **campos):
    """Obra con n unidades hoja y orden ya recalculado."""
    obra = Obra.objects.create(titulo=campos.pop('titulo', slug), slug=slug, **campos)
    unidades = [
        UnidadNarrativa.objects.create(obra=obra, tipo=tipo_unidad, nombre=f'U{i}', orden_local=i)
        for i in range(1, n + 1)
    ]
    obra.recalcular_orden()
    for u in unidades:
        u.refresh_from_db()
    return obra, unidades


def crear_post(autor, obra, referencia, frontera=None, text='post'):
    return Post.objects.create(
        author=autor, obra=obra, text=text,
        referencia_narrativa=referencia, frontera_spoiler=frontera or referencia,
        frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
    )