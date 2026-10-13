"""Admin de narrative por área. Importar los módulos registra sus ModelAdmin;
se reexportan los nombres para no romper importaciones existentes."""

from .comun import (
    CAMPOS_QUE_REORDENAN,
    RELACIONES_UNIDAD,
    ImagenDesdeUrlForm,
    limitar_unidades_a_obra,
    miniatura,
    relaciones_de,
)
from .catalogo import (
    CategoriaAdmin,
    ExternalIdAdmin,
    ObraAdmin,
    ObraAdminForm,
    ObraListadoForm,
    ProgresoUsuarioAdmin,
    TemaTransversalAdmin,
    TemaTransversalAdminForm,
    UnidadNarrativaAdmin,
    UnidadNarrativaAdminForm,
)
from .personajes import (
    ConfianzaFilter,
    EtapaPersonajeForm,
    EtapaPersonajeInline,
    PendientesFilter,
    PersonajeAdmin,
    PersonajeAdminForm,
    PropuestaAparicionAdmin,
    PropuestaAparicionForm,
    PropuestaAparicionInline,
    RelevanciaPersonajeAdmin,
    RelevanciaPersonajeInline,
)
from .solicitudes import (
    SolicitudPersonajeAdmin,
    SolicitudPersonajeForm,
    SolicitudTemaAdmin,
)