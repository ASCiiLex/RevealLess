import yaml
from datetime import date

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
        parser.add_argument(
            '--fechas-volumen', default=None,
            help='YAML {volumen: fecha} — aproxima la fecha de cada capítulo repartiendo '
                 'proporcionalmente el rango "volumenes" del arco entre sus capítulos.',
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
        self.fechas_volumen = self._cargar_fechas_volumen(options.get('fechas_volumen'))

        for nodo in data.get('nodos', []):
            self._construir_nodo(obra, None, nodo)

        for tema in data.get('temas_transversales', []):
            self._construir_tema(obra, tema)

        obra.recalcular_orden()
        self.stdout.write(self.style.SUCCESS(f'Estructura aplicada sobre: {obra.titulo}'))

    def _cargar_fechas_volumen(self, ruta):
        if not ruta:
            return None
        with open(ruta, encoding='utf-8') as f:
            crudo = yaml.safe_load(f)
        return {int(vol): date.fromisoformat(str(fecha)) for vol, fecha in crudo.items()}

    # -- Parte / Saga / Arco / Libro / etc. --------------------------------

    def _construir_nodo(self, obra, padre, nodo):
        # Clave de identidad: (obra, padre, tipo, orden_local) — NUNCA
        # nombre. Un nodo estructural puede cambiar de nombre entre
        # pasadas (p.ej. título de capítulo placeholder -> título real)
        # y debe seguir siendo la misma fila, no duplicarse.
        unidad, creada = UnidadNarrativa.objects.get_or_create(
            obra=obra, padre=padre, tipo=nodo['tipo'], orden_local=nodo['orden_local'],
            defaults={'nombre': nodo['nombre']},
        )
        if not creada and unidad.nombre != nodo['nombre']:
            unidad.nombre = nodo['nombre']
            unidad.save(update_fields=['nombre'])

        # Fecha directa en el propio nodo — caso de curación manual sin
        # Jikan de por medio (Star Wars, LOTR...), donde la fecha real ya
        # se conoce de antemano y no hace falta aproximarla por volumen.
        if 'fecha' in nodo:
            fecha = date.fromisoformat(str(nodo['fecha']))
            if unidad.fecha != fecha:
                unidad.fecha = fecha
                unidad.save(update_fields=['fecha'])

        if 'vincular_episodios' in nodo:
            self._vincular_o_crear(obra, unidad, nodo['vincular_episodios'], tipo='episodio',
                                    nombre_patron='Episodio {n}', hasta=self.hasta_episodio,
                                    flag_hasta='--hasta-episodio', volumenes=None)
        if 'vincular_capitulos' in nodo:
            self._vincular_o_crear(obra, unidad, nodo['vincular_capitulos'], tipo='capitulo',
                                    nombre_patron='Capítulo {n}', hasta=self.hasta_capitulo,
                                    flag_hasta='--hasta-capitulo', volumenes=nodo.get('volumenes'))

        for hijo in nodo.get('hijos', []):
            self._construir_nodo(obra, unidad, hijo)

    def _volumen_para_capitulo(self, n, inicio, fin, volumenes):
        """Reparto proporcional por posición: el primer tramo de capítulos
        cae en el primer volumen del rango, el último tramo en el último.
        Aproximación consciente — no hay tabla capítulo↔volumen exacta."""
        v_inicio, v_fin = volumenes
        if v_inicio is None or v_fin is None:
            return None
        n_capitulos = fin - inicio + 1
        n_volumenes = v_fin - v_inicio + 1
        if n_volumenes <= 1 or n_capitulos <= 1:
            return v_inicio
        idx = min(n_volumenes - 1, (n - inicio) * n_volumenes // n_capitulos)
        return v_inicio + idx

    def _vincular_o_crear(self, obra, arco, rango, tipo, nombre_patron, hasta, flag_hasta, volumenes):
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

        creados, reasignados, con_fecha = 0, 0, 0
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

            if tipo == 'capitulo' and self.fechas_volumen and volumenes:
                volumen = self._volumen_para_capitulo(n, inicio, fin, volumenes)
                fecha = self.fechas_volumen.get(volumen) if volumen else None
                if fecha and unidad.fecha != fecha:
                    unidad.fecha = fecha
                    unidad.save(update_fields=['fecha'])
                    con_fecha += 1

        mensaje = f'{arco.nombre}: {creados} creados como placeholder, {reasignados} reasignados ({inicio}-{fin}).'
        if con_fecha:
            mensaje += f' {con_fecha} con fecha aproximada por volumen.'
        self.stdout.write(mensaje)

    # -- TemaTransversal (temático o minihistoria) ------------------------

    def _construir_tema(self, obra, tema):
        tipo = tema.get('tipo', TemaTransversal.TIPO_TEMATICO)
        tema_obj, creado = TemaTransversal.objects.get_or_create(
            obra=obra, nombre=tema['nombre'], defaults={'tipo': tipo},
        )
        if not creado and tema_obj.tipo != tipo:
            tema_obj.tipo = tipo
            tema_obj.save(update_fields=['tipo'])

        # tipo de las hojas a vincular — 'capitulo' por defecto (histórico),
        # pero una obra de películas (MCU, Star Wars...) usa 'pelicula'.
        tipo_unidad = tema.get('tipo_unidad', 'capitulo')

        unidades = tema.get('unidades')
        if unidades:
            # Lista explícita de orden_local — para temas NO contiguos (un
            # personaje que aparece en películas salteadas a lo largo del
            # catálogo, no un rango seguido).
            qs = UnidadNarrativa.objects.filter(
                obra=obra, tipo=tipo_unidad, orden_local__in=unidades,
            )
            tema_obj.unidades.set(qs)
            encontrados = qs.count()
            aviso = '' if encontrados == len(unidades) else (
                f' (ATENCIÓN: se esperaban {len(unidades)}, encontrados {encontrados} — '
                f'revisa los orden_local)'
            )
            self.stdout.write(f'{tema["nombre"]}: {encontrados} unidades vinculadas por lista explícita.{aviso}')
            return

        rango = tema.get('rango_capitulos')
        if rango:
            inicio, fin = rango
            qs = UnidadNarrativa.objects.filter(obra=obra, tipo=tipo_unidad, orden_local__gte=inicio)
            if fin is not None:
                qs = qs.filter(orden_local__lte=fin)
            tema_obj.unidades.set(qs)
            aviso = ' — RANGO completo, pendiente de afinar a capítulos exactos.' if tema.get('revisar') else ''
            self.stdout.write(self.style.WARNING(f'{tema["nombre"]}: {qs.count()} capítulos vinculados por rango.{aviso}')
                               if tema.get('revisar') else f'{tema["nombre"]}: {qs.count()} capítulos vinculados.')