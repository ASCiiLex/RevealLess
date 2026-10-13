"""Personajes por responsabilidad. Se reexportan todos los nombres para no
cambiar ningún `from narrative.services.personajes import ...`."""

from .apariciones import (
    aplicar_cambio_propuesta,
    aprobar_propuesta,
    eliminar_propuesta,
    rechazar_propuesta,
)
from .fusion import fusionar_personajes
from .identidades import identidad_conocida, identidades_conocidas, ids_con_identidades
from .presentacion import (
    NIVEL_ORDEN_DE_PRESENTACION,
    PESO_POSTS,
    _nivel_con_etapas,
    _superada,
    nombres_conocidos,
    ordenar_por_relevancia,
    presentacion_personaje,
    progreso_por_obra,
)
from .solicitudes import aprobar_solicitud_personaje, proponer_personaje, rechazar_solicitud_personaje