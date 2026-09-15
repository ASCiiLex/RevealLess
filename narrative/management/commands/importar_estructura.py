import yaml
from django.core.management.base import BaseCommand, CommandError

from narrative.models import UnidadNarrativa, TemaTransversal, ExternalId


class Command(BaseCommand):
    help = 'Fase B: aplica un YAML de curación (Parte/Saga/Arco/TemaTransversal) sobre una Obra ya importada.'

    def add_arguments(self, parser):
        parser.add_argument('archivo', help='Ruta al YAML de curación.')
        parser.add_argument(
            '--hasta-capitulo', type=int, default=None,
            help='Cierra los rangos abiertos (fin=null) de vincular_capitulos hasta este número.',
        )
        parser.add_argument(
            '--hasta-episodio', type=int, default=None,
            help='Cierra los rangos abiertos (fin=null) de vincular_episodios hasta este número.',
        )

    def handle(self, *args, **options):
        with open(options['archivo'], encoding='utf-8') as f:
            data = yaml.safe_load(f)

        ancla = data['obra_external_id']
        externo = ExternalId.objects.filter(
            source=ancla['source'], external_id=str(ancla['external_id']), obra__isnull=False
        ).first()
        if not externo:
            raise CommandError(
                f"No hay ninguna Obra con ExternalId {ancla['source']}:{ancla['external_id']}. "
                'Ejecuta primero importar_catalogo (Fase A).'
            )
        obra = externo.obra
        self.hasta_capitulo = options.get('hasta_capitulo')
        self.hasta_episodio = options.get('hasta_episodio')

        for nodo in data.get('nodos', []):
            self._construir_nodo(obra, None, nodo)

        for tema in data.get('temas_transversales', []):
            self._construir_tema(obra, tema)

        obra.recalcular_orden()
        self.stdout.write(self.style.SUCCESS(f'Estructura aplicada sobre: {obra.titulo}'))

    # -- Parte / Saga / Arco ---------------------------------------------

    def _construir_nodo(self, obra, padre, nodo):
        unidad, creada = UnidadNarrativa.objects.get_or_create(
            obra=obra, padre=padre, tipo=nodo['tipo'], nombre=nodo['nombre'],
            defaults={'orden_local': nodo['orden_local']},
        )
        if not creada and unidad.orden_local != nodo['orden_local']:
            unidad.orden_local = nodo['orden_local']
            unidad.save(update_fields=['orden_local'])

        if 'vincular_episodios' in nodo:
            self._vincular_o_crear(obra, unidad, nodo['vincular_episodios'], tipo='episodio',
                                    nombre_patron='Episodio {n}', hasta=self.hasta_episodio,
                                    flag_hasta='--hasta-episodio')
        if 'vincular_capitulos' in nodo:
            self._vincular_o_crear(obra, unidad, nodo['vincular_capitulos'], tipo='capitulo',
                                    nombre_patron='Capítulo {n}', hasta=self.hasta_capitulo,
                                    flag_hasta='--hasta-capitulo')

        for hijo in nodo.get('hijos', []):
            self._construir_nodo(obra, unidad, hijo)

    def _vincular_o_crear(self, obra, arco, rango, tipo, nombre_patron, hasta, flag_hasta):
        """Común a episodios (anime) y capítulos (manga): si la hoja ya
        existe (importada por Jikan en Fase A, o creada en una pasada
        anterior de este mismo comando), se reasigna a este arco. Si no
        existe todavía, se crea como placeholder — así el árbol completo
        queda operativo aunque Fase A no haya podido traer los datos
        reales, y cuando Fase A sí los traiga más tarde adoptará estas
        mismas hojas por su orden_local en vez de duplicarlas."""
        inicio, fin = rango
        if fin is None:
            fin = hasta
            if fin is None:
                self.stdout.write(self.style.WARNING(
                    f'{arco.nombre}: rango abierto sin {flag_hasta} — se omite.'
                ))
                return

        creados, reasignados = 0, 0
        for n in range(inicio, fin + 1):
            unidad, creada = UnidadNarrativa.objects.get_or_create(
                obra=obra, tipo=tipo, orden_local=n,
                defaults={'padre': arco, 'nombre': nombre_patron.format(n=n)},
            )
            if creada:
                creados += 1
            else:
                if unidad.padre_id != arco.id:
                    unidad.padre = arco
                    unidad.save(update_fields=['padre'])
                reasignados += 1

        self.stdout.write(f'{arco.nombre}: {creados} creados como placeholder, {reasignados} reasignados ({inicio}-{fin}).')

    # -- TemaTransversal (temático o minihistoria) ------------------------

    def _construir_tema(self, obra, tema):
        tipo = tema.get('tipo', TemaTransversal.TIPO_TEMATICO)
        tema_obj, creado = TemaTransversal.objects.get_or_create(
            obra=obra, nombre=tema['nombre'], defaults={'tipo': tipo},
        )
        if not creado and tema_obj.tipo != tipo:
            tema_obj.tipo = tipo
            tema_obj.save(update_fields=['tipo'])

        rango = tema.get('rango_capitulos')
        if rango:
            inicio, fin = rango
            qs = UnidadNarrativa.objects.filter(obra=obra, tipo='capitulo', orden_local__gte=inicio)
            if fin is not None:
                qs = qs.filter(orden_local__lte=fin)
            tema_obj.unidades.set(qs)
            aviso = ' — RANGO completo, pendiente de afinar a capítulos exactos.' if tema.get('revisar') else ''
            self.stdout.write(self.style.WARNING(f'{tema["nombre"]}: {qs.count()} capítulos vinculados por rango.{aviso}')
                               if tema.get('revisar') else f'{tema["nombre"]}: {qs.count()} capítulos vinculados.')