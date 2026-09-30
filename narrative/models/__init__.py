"""Reexporta todos los modelos para mantener `from narrative.models import X`
y las rutas que referencian las migraciones existentes."""

from .catalogo import (
    Categoria,
    Obra,
    UnidadNarrativa,
    obra_image_path,
    unidad_image_path,
)
from .importacion import ExternalId
from .progreso import ProgresoUsuario
from .temas import TemaTransversal, SolicitudTema
from .personajes import Personaje
from .clasificacion import ClasificacionNarrativa

__all__ = [
    'Categoria',
    'Obra',
    'UnidadNarrativa',
    'obra_image_path',
    'unidad_image_path',
    'ExternalId',
    'ProgresoUsuario',
    'TemaTransversal',
    'SolicitudTema',
    'Personaje',
    'ClasificacionNarrativa',
]