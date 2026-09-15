from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from django.utils.dateparse import parse_datetime

from narrative.models import Obra, UnidadNarrativa, ExternalId
from narrative.services import jikan_client as jikan

# Jikan 'type' -> Obra.tipo. Lo que no aparece aquí cae en TIPO_SERIE con aviso.
MAPA_TIPO_ANIME = {
    'TV': Obra.TIPO_SERIE,
    'Movie': Obra.TIPO_PELICULA,
    'OVA': Obra.TIPO_OVA,
    'ONA': Obra.TIPO_OVA,
    'Special': Obra.TIPO_ESPECIAL,
    'Music': Obra.TIPO_CORTO,
}

# Relations que sí consideramos indicio fiable de adaptación entre
# continuidades. El resto (Sequel, Prequel, Side story, Summary...) queda
# fuera: son relaciones dentro de la MISMA continuidad, no adapta_a.
RELACIONES_ADAPTACION = {'Adaptation', 'Alternative version', 'Full story', 'Parent story'}


class Command(BaseCommand):
    help = 'Fase A: importa una Obra y sus episodios (si aplica) desde Jikan.'

    def add_arguments(self, parser):
        parser.add_argument('--source', default='jikan', choices=['jikan'])
        parser.add_argument('--tipo', required=True, choices=['anime', 'manga'],
                             help='Endpoint de Jikan a consultar.')
        parser.add_argument('--external-id', required=True, type=int, help='MAL ID.')
        parser.add_argument('--slug', help='Slug a usar. Por defecto, derivado del título.')

    def handle(self, *args, **options):
        source = options['source']
        tipo_endpoint = options['tipo']
        mal_id = options['external_id']

        obra = self._obra_existente(source, mal_id)
        if tipo_endpoint == 'anime':
            data = jikan.get_anime(mal_id)
            obra = self._actualizar_desde_anime(obra, data, options.get('slug'))
        else:
            data = jikan.get_manga(mal_id)
            obra = self._actualizar_desde_manga(obra, data, options.get('slug'))

        ExternalId.objects.update_or_create(
            source=source, obra=obra,
            defaults={'external_id': str(mal_id)},
        )
        self.stdout.write(self.style.SUCCESS(f'Obra: {obra.titulo} ({obra.get_tipo_display()})'))

        if tipo_endpoint == 'anime':
            self._importar_episodios(obra, source, mal_id, data.get('episodes'))

        self._enlazar_adaptaciones(obra, source, mal_id, tipo_endpoint)

        if tipo_endpoint == 'anime':
            obra.recalcular_orden()
            self.stdout.write(self.style.SUCCESS('orden_inicio/orden_fin recalculados.'))
        else:
            self.stdout.write(self.style.WARNING(
                'Manga sin capítulos importados (Jikan no los expone). '
                'Usa el comando importar_estructura para crearlos vía curación manual.'
            ))

    # -- localización idempotente -------------------------------------

    def _obra_existente(self, source, mal_id):
        externo = ExternalId.objects.filter(source=source, external_id=str(mal_id), obra__isnull=False).first()
        return externo.obra if externo else Obra()

    # -- mapeo de campos ------------------------------------------------

    def _slug_unico(self, obra, titulo, tipo, slug_forzado):
        base = slug_forzado or slugify(titulo)
        candidato = base
        qs = Obra.objects.exclude(pk=obra.pk) if obra.pk else Obra.objects.all()
        if qs.filter(slug=candidato).exists():
            candidato = slugify(f'{titulo}-{tipo}')
        return candidato

    def _fecha(self, iso_string):
        if not iso_string:
            return None
        dt = parse_datetime(iso_string)
        return dt.date() if dt else None

    def _actualizar_desde_anime(self, obra, data, slug_forzado):
        tipo = MAPA_TIPO_ANIME.get(data.get('type'))
        if tipo is None:
            self.stdout.write(self.style.WARNING(
                f"Tipo Jikan '{data.get('type')}' sin mapeo — se usa 'serie' por defecto."
            ))
            tipo = Obra.TIPO_SERIE

        obra.titulo = data['title']
        if not obra.pk:
            obra.slug = self._slug_unico(obra, obra.titulo, tipo, slug_forzado)
        obra.tipo = tipo
        obra.sinopsis = data.get('synopsis') or ''
        obra.fecha_publicacion = self._fecha((data.get('aired') or {}).get('from'))
        # Aproximación: Jikan no da el autor original en el endpoint de
        # anime, solo estudio(s) de producción. Queda marcado como tal.
        estudios = ', '.join(s['name'] for s in data.get('studios', []))
        obra.autor = f'Estudio: {estudios}' if estudios else ''
        obra.save()
        return obra

    def _actualizar_desde_manga(self, obra, data, slug_forzado):
        obra.titulo = data['title']
        if not obra.pk:
            obra.slug = self._slug_unico(obra, obra.titulo, Obra.TIPO_MANGA, slug_forzado)
        obra.tipo = Obra.TIPO_MANGA
        obra.sinopsis = data.get('synopsis') or ''
        obra.fecha_publicacion = self._fecha((data.get('published') or {}).get('from'))
        obra.autor = ', '.join(a['name'] for a in data.get('authors', []))
        obra.save()
        return obra

    # -- episodios (solo anime) -----------------------------------------

    def _importar_episodios(self, obra, source, mal_id, total_episodios):
        episodios, paginas_fallidas = jikan.get_anime_episodes(mal_id, total_episodios)

        creados, actualizados = 0, 0
        for ep in episodios:
            ep_id = ep['mal_id']
            nombre = ep.get('title') or f'Episodio {ep_id}'
            fecha = self._fecha(ep.get('aired'))

            externo = ExternalId.objects.filter(
                source=source, external_id=str(ep_id), unidad__obra=obra
            ).first()
            if externo:
                unidad = externo.unidad
                unidad.nombre = nombre
                unidad.fecha = fecha
                unidad.save(update_fields=['nombre', 'fecha'])
                actualizados += 1
                continue

            unidad = UnidadNarrativa.objects.create(
                obra=obra, padre=None, tipo='episodio',
                nombre=nombre, orden_local=ep_id, fecha=fecha,
            )
            ExternalId.objects.create(source=source, external_id=str(ep_id), unidad=unidad)
            creados += 1

        self.stdout.write(self.style.SUCCESS(f'Episodios: {creados} creados, {actualizados} actualizados.'))

        if paginas_fallidas:
            self.stdout.write(self.style.WARNING(
                f'{len(paginas_fallidas)} página(s) fallaron tras los reintentos: {paginas_fallidas}. '
                'MyAnimeList puede estar lento para esta obra en concreto (habitual en series muy largas). '
                'El comando es idempotente — vuelve a ejecutarlo más tarde, solo rellenará lo que falte.'
            ))

    # -- adapta_a por relations (mejor esfuerzo) -------------------------

    def _enlazar_adaptaciones(self, obra, source, mal_id, tipo_endpoint):
        if obra.adapta_a_id:
            return
        try:
            relaciones = jikan.get_relations(mal_id, tipo_endpoint)
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'No se pudieron consultar relations: {exc}'))
            return

        for grupo in relaciones:
            if grupo.get('relation') not in RELACIONES_ADAPTACION:
                continue
            for entrada in grupo.get('entry', []):
                if entrada.get('type') == tipo_endpoint:
                    continue  # misma continuidad, no cruza tipo — se ignora
                externo = ExternalId.objects.filter(
                    source=source, external_id=str(entrada['mal_id']), obra__isnull=False
                ).first()
                if not externo:
                    self.stdout.write(self.style.WARNING(
                        f"Relación '{grupo['relation']}' hacia \"{entrada['name']}\" "
                        f"(MAL {entrada['mal_id']}) — no importada todavía, se omite adapta_a."
                    ))
                    continue
                obra.adapta_a = externo.obra
                obra.save(update_fields=['adapta_a'])
                self.stdout.write(self.style.SUCCESS(
                    f'adapta_a → {externo.obra.titulo} (vía relación "{grupo["relation"]}")'
                ))
                return