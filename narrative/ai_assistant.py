import logging

logger = logging.getLogger(__name__)

CONFIANZA_MINIMA = 0.6


class SugerenciaIA:
    def __init__(self, frontera_spoiler=None, confianza=0.0):
        self.frontera_spoiler = frontera_spoiler
        self.confianza = confianza

    @property
    def es_utilizable(self):
        return self.frontera_spoiler is not None and self.confianza >= CONFIANZA_MINIMA


def proponer_clasificacion(texto, obra, unidad_autor):
    """Punto único de entrada al asistente de IA. Nunca lanza excepción hacia
    fuera: cualquier fallo (API caída, timeout, proveedor sin configurar)
    se traduce en una sugerencia no utilizable, y quien llama cae al
    fallback (progreso del autor) sin bloquear la publicación.
    """
    try:
        return _llamar_api(texto, obra, unidad_autor)
    except Exception:
        logger.exception('Fallo al llamar a la API de IA de clasificación')
        return SugerenciaIA()


def _llamar_api(texto, obra, unidad_autor):
    """TODO: implementar la llamada real una vez decidido el proveedor
    (Anthropic/OpenAI/otro). Debe devolver un SugerenciaIA con
    frontera_spoiler como instancia de UnidadNarrativa (o None) y
    confianza entre 0 y 1. Mientras tanto, NotImplementedError se
    captura arriba y produce fallback automático."""
    raise NotImplementedError('Proveedor de IA todavía no configurado.')