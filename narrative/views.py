from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Obra, ProgresoUsuario
from .forms import SeleccionarObraForm, ProgresoForm
from .services import SaltoGrandeRequiereConfirmacion


@login_required
def seleccionar_obra(request):
    if request.method == 'POST':
        form = SeleccionarObraForm(request.POST)
        if form.is_valid():
            obra = form.cleaned_data['obra']
            tiene_progreso = ProgresoUsuario.objects.filter(
                usuario=request.user, obra=obra
            ).exists()

            create_url = reverse('create_post', kwargs={'obra_slug': obra.slug})
            if tiene_progreso:
                return redirect(create_url)

            progreso_url = reverse('narrative_declarar_progreso', kwargs={'obra_slug': obra.slug})
            return redirect(f'{progreso_url}?next={create_url}')
    else:
        form = SeleccionarObraForm()
    return render(request, 'narrative/select_obra.html', {'form': form})


@login_required
def declarar_progreso(request, obra_slug):
    obra = get_object_or_404(Obra, slug=obra_slug)

    next_url = request.GET.get('next', '')
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = reverse('feed')

    if request.method == 'POST':
        form = ProgresoForm(request.POST, obra=obra)
        if form.is_valid():
            try:
                form.guardar(request.user)
            except SaltoGrandeRequiereConfirmacion as exc:
                form.add_error(
                    'confirmar_salto',
                    f'Vas a saltar {exc.salto} posiciones de golpe. Marca la casilla para confirmarlo.'
                )
            else:
                return redirect(next_url)
    else:
        form = ProgresoForm(obra=obra)

    return render(request, 'narrative/set_progreso.html', {
        'form': form, 'obra': obra, 'next': next_url,
    })


@login_required
def progreso_react_view(request, obra_slug):
    get_object_or_404(Obra, slug=obra_slug)
    return render(request, 'narrative/progreso_react.html', {'obra_slug': obra_slug})


@login_required
def obra_landing_react_view(request, obra_slug):
    """Vista mínima que monta el punto de entrada de React para la
    landing de obra (Fase 4)."""
    get_object_or_404(Obra, slug=obra_slug)
    return render(request, 'narrative/obra_landing_react.html', {'obra_slug': obra_slug})


@login_required
def obra_temas_react_view(request, obra_slug):
    """Vista mínima para la página de Temas de una obra, mudada aquí
    desde la landing: hoy la landing embebe el gestor de progreso
    directamente, y Temas pasa a ser su propia pantalla, igual que
    antes lo era Progreso."""
    get_object_or_404(Obra, slug=obra_slug)
    return render(request, 'narrative/obra_temas_react.html', {'obra_slug': obra_slug})