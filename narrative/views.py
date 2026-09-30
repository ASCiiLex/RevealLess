from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Categoria, Obra, TemaTransversal


@login_required
def progreso_react_view(request, obra_slug):
    get_object_or_404(Obra, slug=obra_slug)
    return render(request, 'narrative/progreso_react.html', {'obra_slug': obra_slug})


@login_required
def obra_landing_react_view(request, obra_slug):
    """Monta React para la landing de obra."""
    get_object_or_404(Obra, slug=obra_slug)
    return render(request, 'narrative/obra_landing_react.html', {'obra_slug': obra_slug})


@login_required
def obra_temas_react_view(request, obra_slug):
    """Monta React para la pantalla de Temas de una obra."""
    get_object_or_404(Obra, slug=obra_slug)
    return render(request, 'narrative/obra_temas_react.html', {'obra_slug': obra_slug})


@login_required
def tema_landing_react_view(request, tema_id):
    """Monta React para la landing de un tema transversal."""
    get_object_or_404(TemaTransversal, id=tema_id)
    return render(request, 'narrative/tema_landing_react.html', {'tema_id': tema_id})


@login_required
def categoria_landing_react_view(request, categoria_id):
    """Monta React para la landing de una categoría."""
    get_object_or_404(Categoria, id=categoria_id)
    return render(request, 'narrative/categoria_landing_react.html', {'categoria_id': categoria_id})