from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def publicar_react_view(request):
    """Monta React para el flujo unificado de publicar: obra -> progreso -> post."""
    return render(request, 'posts/publicar_react.html')