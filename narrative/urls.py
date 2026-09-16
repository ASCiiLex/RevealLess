from django.urls import path
from . import views
from .api_views import FeedAPIView, ProgresoAPIView
from .api_views_catalog import (
    CatalogoObrasAPIView,
    ObraDetalleAPIView,
    ObraLandingAPIView,
    SolicitudTemaListCreateAPIView,
    BuscarAPIView,
)

urlpatterns = [
    path('publicar/', views.seleccionar_obra, name='narrative_seleccionar_obra'),
    path('progreso/<slug:obra_slug>/', views.declarar_progreso, name='narrative_declarar_progreso'),
    path('progreso-react/<slug:obra_slug>/', views.progreso_react_view, name='narrative_progreso_react'),
    path('obra/<slug:obra_slug>/react/', views.obra_landing_react_view, name='narrative_obra_landing_react'),
    path('obra/<slug:obra_slug>/temas/react/', views.obra_temas_react_view, name='narrative_obra_temas_react'),

    path('api/feed/', FeedAPIView.as_view(), name='narrative_api_feed'),
    path('api/progreso/<slug:obra_slug>/', ProgresoAPIView.as_view(), name='narrative_api_progreso'),
    path('api/obras/', CatalogoObrasAPIView.as_view(), name='narrative_api_obras'),
    path('api/obras/<slug:obra_slug>/detalle/', ObraDetalleAPIView.as_view(), name='narrative_api_obra_detalle'),
    path('api/obras/<slug:obra_slug>/landing/', ObraLandingAPIView.as_view(), name='narrative_api_obra_landing'),
    path('api/solicitudes-tema/', SolicitudTemaListCreateAPIView.as_view(), name='narrative_api_solicitudes_tema'),
    path('api/buscar/', BuscarAPIView.as_view(), name='narrative_api_buscar'),
]