from django.urls import path
from . import views

urlpatterns = [
    path('publicar/', views.seleccionar_obra, name='narrative_seleccionar_obra'),
    path('progreso/<slug:obra_slug>/', views.declarar_progreso, name='narrative_declarar_progreso'),
]