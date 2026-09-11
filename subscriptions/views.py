from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def suscripciones_react_view(request):
    """Vista mínima que monta el punto de entrada de React para la
    gestión de suscripciones (Fase 4). Mismo patrón que feed_react_view
    y progreso_react_view: HTML casi vacío, toda la lógica vive en
    api/suscripciones/ y api/obras/<slug>/detalle/."""
    return render(request, 'subscriptions/suscripciones_react.html')