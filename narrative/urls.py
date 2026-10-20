from django.urls import path

from . import views
from .api_views import (
    FeedAPIView,
    ProgresoAPIView,
    ProgresoExisteAPIView,
    CatalogoObrasAPIView,
    ObrasPublicarAPIView,
    PersonajesPublicarAPIView,
    ObraDetalleAPIView,
    ObraLandingAPIView,
    TemaLandingAPIView,
    CategoriaLandingAPIView,
    PersonajeLandingAPIView,
    SolicitudTemaListCreateAPIView,
    ArcoAPIView,
    BuscarAPIView,
    UnidadesBuscarAPIView,
    ObraContextoPublicarAPIView,
)

urlpatterns = [
    path('progreso/<slug:obra_slug>/', views.progreso_react_view, name='narrative_progreso'),
    path('obra/<slug:obra_slug>/', views.obra_landing_react_view, name='narrative_obra_landing'),
    path('obra/<slug:obra_slug>/temas/', views.obra_temas_react_view, name='narrative_obra_temas'),
    path('tema/<int:tema_id>/', views.tema_landing_react_view, name='narrative_tema_landing'),
    path('categoria/<int:categoria_id>/', views.categoria_landing_react_view, name='narrative_categoria_landing'),
    path('personaje/<int:personaje_id>/', views.personaje_landing_react_view, name='narrative_personaje_landing'),

    path('api/feed/', FeedAPIView.as_view(), name='narrative_api_feed'),
    path('api/progreso/<slug:obra_slug>/', ProgresoAPIView.as_view(), name='narrative_api_progreso'),
    path('api/progreso/<slug:obra_slug>/existe/', ProgresoExisteAPIView.as_view(), name='narrative_api_progreso_existe'),
    path('api/obras/', CatalogoObrasAPIView.as_view(), name='narrative_api_obras'),
    path('api/obras/publicar/', ObrasPublicarAPIView.as_view(), name='narrative_api_obras_publicar'),
    path('api/obras/<slug:obra_slug>/detalle/', ObraDetalleAPIView.as_view(), name='narrative_api_obra_detalle'),
    path('api/obras/<slug:obra_slug>/landing/', ObraLandingAPIView.as_view(), name='narrative_api_obra_landing'),
    path('api/obras/<slug:obra_slug>/unidades/', UnidadesBuscarAPIView.as_view(), name='narrative_api_unidades_buscar'),
    path('api/obras/<slug:obra_slug>/personajes-publicar/', PersonajesPublicarAPIView.as_view(), name='narrative_api_personajes_publicar'),
    path('api/obras/<slug:obra_slug>/contexto-publicar/', ObraContextoPublicarAPIView.as_view(), name='narrative_api_obra_contexto_publicar'),
    path('api/temas/<int:tema_id>/', TemaLandingAPIView.as_view(), name='narrative_api_tema_landing'),
    path('api/categorias/<int:categoria_id>/', CategoriaLandingAPIView.as_view(), name='narrative_api_categoria_landing'),
    path('api/personajes/<int:personaje_id>/', PersonajeLandingAPIView.as_view(), name='narrative_api_personaje_landing'),
    path('api/arcos/<int:unidad_id>/', ArcoAPIView.as_view(), name='narrative_api_arco'),
    path('api/solicitudes-tema/', SolicitudTemaListCreateAPIView.as_view(), name='narrative_api_solicitudes_tema'),
    path('api/buscar/', BuscarAPIView.as_view(), name='narrative_api_buscar'),
]