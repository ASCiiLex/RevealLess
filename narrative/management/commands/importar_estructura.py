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
            self._vincular_episodios(obra, unidad, nodo['vincular_episodios'])
        if 'vincular_capitulos' in nodo:
            self._vincular_capitulos(obra, unidad, nodo['vincular_capitulos'])

        for hijo in nodo.get('hijos', []):
            self._construir_nodo(obra, unidad, hijo)

    def _vincular_episodios(self, obra, arco, rango):
        inicio, fin = rango
        qs = UnidadNarrativa.objects.filter(obra=obra, padre__isnull=True, tipo='episodio', orden_local__gte=inicio)
        if fin is not None:
            qs = qs.filter(orden_local__lte=fin)
        total = qs.update(padre=arco)
        if total == 0:
            self.stdout.write(self.style.WARNING(
                f'{arco.nombre}: 0 episodios encontrados en el rango {rango} '
                '— ¿se ejecutó importar_catalogo para esta Obra?'
            ))
        else:
            self.stdout.write(f'{arco.nombre}: {total} episodios reasignados.')

    def _vincular_capitulos(self, obra, arco, rango):
        inicio, fin = rango
        if fin is None:
            fin = self.hasta_capitulo
            if fin is None:
                self.stdout.write(self.style.WARNING(
                    f'{arco.nombre}: rango abierto sin --hasta-capitulo — se omite.'
                ))
                return

        creados = 0
        for n in range(inicio, fin + 1):
            unidad, creada = UnidadNarrativa.objects.get_or_create(
                obra=obra, tipo='capitulo', orden_local=n,
                defaults={'padre': arco, 'nombre': f'Capítulo {n}'},
            )
            if not creada and unidad.padre_id != arco.id:
                unidad.padre = arco
                unidad.save(update_fields=['padre'])
            if creada:
                creados += 1
        self.stdout.write(f'{arco.nombre}: {creados} capítulos creados ({inicio}-{fin}).')

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