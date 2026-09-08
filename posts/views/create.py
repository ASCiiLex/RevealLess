from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from ..forms import PostForm
from narrative.models import Obra, ProgresoUsuario, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from narrative.ai_assistant import proponer_clasificacion


@login_required
def create_post(request, obra_slug):
    obra = get_object_or_404(Obra, slug=obra_slug)
    progreso = ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).first()

    if not progreso:
        create_url = reverse('create_post', kwargs={'obra_slug': obra.slug})
        progreso_url = reverse('narrative_declarar_progreso', kwargs={'obra_slug': obra.slug})
        return redirect(f'{progreso_url}?next={create_url}')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, obra=obra)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.obra = obra

            if form.cleaned_data.get('frontera_spoiler'):
                new_post.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO
            else:
                sugerencia = proponer_clasificacion(new_post.text, obra, progreso.unidad_actual)
                if sugerencia.es_utilizable:
                    new_post.frontera_spoiler = sugerencia.frontera_spoiler
                    new_post.frontera_origen = ClasificacionNarrativa.ORIGEN_IA
                    new_post.ia_confianza = sugerencia.confianza
                    new_post.clasificado_en = timezone.now()
                else:
                    new_post.frontera_spoiler = progreso.unidad_actual
                    new_post.frontera_origen = ClasificacionNarrativa.ORIGEN_FALLBACK

            try:
                new_post.full_clean()
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                new_post.save()

                nuevo_progreso = form.cleaned_data.get('nuevo_progreso')
                if nuevo_progreso:
                    actualizar_progreso(request.user, obra, nuevo_progreso)

                return redirect('profile', username=request.user.username)
    else:
        form = PostForm(obra=obra)

    return render(request, 'posts/create_post.html', {'form': form, 'obra': obra})