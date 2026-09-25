from django.urls import path
from . import views
from .api_views import FeedAPIView, ProgresoAPIView, ProgresoExisteAPIView
from .api_views_catalog import (
    CatalogoObrasAPIView,
    ObraDetalleAPIView,
    ObraLandingAPIView,
    TemaLandingAPIView,
    SolicitudTemaListCreateAPIView,
    BuscarAPIView,
    UnidadesBuscarAPIView,
    ObraContextoPublicarAPIView,
    
)

urlpatterns = [
    path('progreso/<slug:obra_slug>/', views.progreso_react_view, name='narrative_progreso'),
    path('obra/<slug:obra_slug>/', views.obra_landing_react_view, name='narrative_obra_landing'),
    path('obra/<slug:obra_slug>/temas/', views.obra_temas_react_view, name='narrative_obra_temas'),
    path('tema/<int:tema_id>/', views.tema_landing_react_view, name='narrative_tema_landing'),

    path('api/feed/', FeedAPIView.as_view(), name='narrative_api_feed'),
    path('api/progreso/<slug:obra_slug>/', ProgresoAPIView.as_view(), name='narrative_api_progreso'),
    path('api/obras/', CatalogoObrasAPIView.as_view(), name='narrative_api_obras'),
    path('api/obras/<slug:obra_slug>/detalle/', ObraDetalleAPIView.as_view(), name='narrative_api_obra_detalle'),
    path('api/obras/<slug:obra_slug>/landing/', ObraLandingAPIView.as_view(), name='narrative_api_obra_landing'),
    path('api/temas/<int:tema_id>/', TemaLandingAPIView.as_view(), name='narrative_api_tema_landing'),
    path('api/solicitudes-tema/', SolicitudTemaListCreateAPIView.as_view(), name='narrative_api_solicitudes_tema'),
    path('api/buscar/', BuscarAPIView.as_view(), name='narrative_api_buscar'),
    path('api/obras/<slug:obra_slug>/unidades/', UnidadesBuscarAPIView.as_view(), name='narrative_api_unidades_buscar'),
    path('api/obras/<slug:obra_slug>/contexto-publicar/', ObraContextoPublicarAPIView.as_view(), name='narrative_api_obra_contexto_publicar'),
    path('api/progreso/<slug:obra_slug>/existe/', ProgresoExisteAPIView.as_view(), name='narrative_api_progreso_existe'),
]