from django.urls import path
from . import views
from .api_views import FeedAPIView, ProgresoAPIView
from .api_views_catalog import CatalogoObrasAPIView

urlpatterns = [
    path('publicar/', views.seleccionar_obra, name='narrative_seleccionar_obra'),
    path('progreso/<slug:obra_slug>/', views.declarar_progreso, name='narrative_declarar_progreso'),
    path('progreso-react/<slug:obra_slug>/', views.progreso_react_view, name='narrative_progreso_react'),

    path('api/feed/', FeedAPIView.as_view(), name='narrative_api_feed'),
    path('api/progreso/<slug:obra_slug>/', ProgresoAPIView.as_view(), name='narrative_api_progreso'),
    path('api/obras/', CatalogoObrasAPIView.as_view(), name='narrative_api_obras'),
]