"""Contenido de demo para la defensa: obras, unidades, previos, progresos y publicaciones desde un YAML.
Idempotente: reutiliza crear_obra_manual, importar_estructura y crear_previo, y no duplica nada."""

from datetime import date
from pathlib import Path

import yaml
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from core.imagenes.remotas import descargar_imagen
from narrative.models import Categoria, ClasificacionNarrativa, ExternalId, Obra, ProgresoUsuario, UnidadNarrativa
from narrative.services import asegurar_unidad_previa, calcular_orden_absoluto
from narrative.services.previos import crear_previo
from posts.models import Post
from posts.videos import VideoNoValido, aplicar_video, resolver_video

ARCHIVO_POR_DEFECTO = 'narrative/data/demo.yaml'
SEPARADOR_PADRE = ' · '
PREVIO = UnidadNarrativa.TIPO_PREVIO


def _fecha(valor):
    if valor is None or isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor))


class Command(BaseCommand):
    help = 'Carga el contenido de demo (obras, previos, progresos y publicaciones) desde un YAML. Idempotente.'

    def add_arguments(self, parser):
        parser.add_argument('archivo', nargs='?', default=ARCHIVO_POR_DEFECTO)
        parser.add_argument('--rehacer', action='store_true', help='Borra y vuelve a crear las publicaciones de demo.')
        parser.add_argument('--sin-progresos', action='store_true', help='No toca el progreso de las cuentas de demo.')

    def handle(self, *args, **opciones):
        ruta = Path(opciones['archivo'])
        with open(ruta, encoding='utf-8') as f:
            datos = yaml.safe_load(f) or {}
        self.carpeta = ruta.parent
        self.creadas = self.existentes = self.avisos = 0

        for obra in datos.get('obras', []):
            self._obra(obra)
        for unidad in datos.get('unidades', []):
            self._unidad_extra(unidad)
        for previo in datos.get('previos', []):
            self._previo(previo)
        if not opciones['sin_progresos']:
            for progreso in datos.get('progresos', []):
                self._progreso(progreso)
        for publicacion in datos.get('publicaciones', []):
            self._publicacion(publicacion, opciones['rehacer'])

        self.stdout.write(self.style.SUCCESS(
            f'Publicaciones: {self.creadas} creadas, {self.existentes} ya existían, {self.avisos} con aviso.'
        ))

    # -- búsquedas -------------------------------------------------------

    def _obra_por_slug(self, slug):
        obra = Obra.objects.filter(slug=slug).first()
        if obra is None:
            raise CommandError(f'No existe la obra «{slug}».')
        return obra

    def _usuario(self, username):
        usuario = User.objects.filter(username=username).first()
        if usuario is None:
            raise CommandError(f'No existe la cuenta «{username}»: créala desde la web.')
        return usuario

    def _unidad(self, obra, ref):
        """Por id, {tipo, orden_local}, nombre exacto o «Padre · Nombre». Nunca un previo."""
        unidades = obra.unidades.select_related('padre')
        if isinstance(ref, int):
            unidades = unidades.filter(id=ref)
        elif isinstance(ref, dict):
            unidades = unidades.filter(tipo=ref['tipo'], orden_local=ref['orden_local'])
        else:
            texto = str(ref).strip()
            if SEPARADOR_PADRE in texto:
                padre, nombre = texto.rsplit(SEPARADOR_PADRE, 1)
                unidades = unidades.filter(nombre__iexact=nombre, padre__nombre__iexact=padre)
            else:
                unidades = unidades.filter(nombre__iexact=texto)
        encontradas = list(unidades.exclude(tipo=PREVIO)[:2])
        if len(encontradas) != 1:
            motivo = 'no existe' if not encontradas else 'es ambigua (usa «Padre · Nombre» o el id)'
            raise CommandError(f'La unidad {ref!r} {motivo} en {obra.titulo}.')
        return encontradas[0]

    def _previo_de(self, obra, ref):
        unidad = self._unidad(obra, ref)
        previo = obra.unidades.filter(tipo=PREVIO, padre_id=unidad.padre_id, orden_local=unidad.orden_local).first()
        if previo is None:
            raise CommandError(f'Falta el previo de «{unidad.nombre}»: añádelo en «previos».')
        return previo

    def _previo_inicial(self, obra):
        previo = obra.unidades.filter(tipo=PREVIO).order_by('orden_inicio').first()
        if previo is None:
            raise CommandError(f'{obra.titulo} no tiene previo: marca la obra con previo_inicial.')
        return previo

    def _posicion(self, obra, datos):
        """Unidad de una frontera o un progreso: previo_de, previo, hasta_previo_de o unidad."""
        if datos.get('previo_de'):
            return self._previo_de(obra, datos['previo_de'])
        if datos.get('previo'):
            return self._previo_inicial(obra)
        if datos.get('hasta_previo_de'):
            # La hoja justo antes del previo: quien llega ahí ya lo ve. En obra nueva, el propio previo.
            previo = self._previo_de(obra, datos['hasta_previo_de'])
            posicion = previo.orden_frontera
            if posicion == 0:
                return previo
            hoja = obra.unidades.filter(orden_inicio=posicion, orden_fin=posicion, hijos__isnull=True).first()
            if hoja is None:
                raise CommandError(f'No hay ninguna unidad en la posición {posicion} de {obra.titulo}.')
            return hoja
        return self._unidad(obra, datos['unidad'])

    # -- pasos -------------------------------------------------------------

    def _obra(self, datos):
        slug = datos['slug']
        if not Obra.objects.filter(slug=slug).exists():
            # Las obras que solo existen en un entorno (p. ej. sugeridas y aprobadas en local) se crean aquí.
            if not datos.get('titulo'):
                raise CommandError(f'La obra «{slug}» no existe y no tiene «titulo» para crearla.')
            argumentos = ['--slug', slug, '--titulo', datos['titulo'], '--tipo', datos.get('tipo', Obra.TIPO_SERIE)]
            for categoria in datos.get('categorias', []):
                argumentos += ['--categoria', categoria]
            if datos.get('sinopsis'):
                argumentos += ['--sinopsis', datos['sinopsis']]
            if datos.get('sin_sufijo'):
                argumentos.append('--sin-sufijo')
            call_command('crear_obra_manual', *argumentos, stdout=self.stdout)
        obra = Obra.objects.get(slug=slug)

        # Las obras sugeridas por usuarios no tienen ExternalId: importar_estructura lo necesita.
        ExternalId.objects.get_or_create(source=ExternalId.SOURCE_MANUAL, external_id=slug, obra=obra)
        for nombre in datos.get('categorias', []):
            obra.categorias.add(Categoria.objects.get_or_create(nombre=nombre)[0])
        if datos.get('adapta_a') and not obra.adapta_a_id:
            obra.adapta_a = self._obra_por_slug(datos['adapta_a'])
            obra.save(update_fields=['adapta_a'])
        if datos.get('portada') and not obra.imagen:
            try:
                obra.imagen = descargar_imagen(datos['portada'])
                obra.save()
            except ValidationError as exc:
                self._avisar(f'Portada de {obra.titulo}: {exc.messages[0]}')

        if datos.get('estructura'):
            call_command('importar_estructura', str(self.carpeta / datos['estructura']), stdout=self.stdout)
        if datos.get('previo_inicial'):
            asegurar_unidad_previa(obra)

    def _unidad_extra(self, datos):
        obra = self._obra_por_slug(datos['obra'])
        padre = self._unidad(obra, datos['padre']) if datos.get('padre') else None
        unidad = obra.unidades.filter(padre=padre, tipo=datos['tipo'], orden_local=datos['orden_local']).first()
        if unidad is None:
            ocupada = obra.unidades.filter(padre=padre, orden_local=datos['orden_local']).exclude(tipo=PREVIO).first()
            if ocupada:
                raise CommandError(f'La posición {datos["orden_local"]} ya la ocupa «{ocupada.nombre}» en {obra.titulo}.')
            unidad = UnidadNarrativa.objects.create(
                obra=obra, padre=padre, tipo=datos['tipo'], orden_local=datos['orden_local'],
                nombre=datos['nombre'], fecha=_fecha(datos.get('fecha')), traducido=True,
            )
        elif unidad.nombre != datos['nombre'] or unidad.fecha != _fecha(datos.get('fecha')):
            unidad.nombre = datos['nombre']
            unidad.fecha = _fecha(datos.get('fecha'))
            unidad.save(update_fields=['nombre', 'fecha'])
        obra.recalcular_orden()
        self.stdout.write(f'Unidad: {obra.titulo} · {unidad.nombre}')

    def _previo(self, datos):
        obra = self._obra_por_slug(datos['obra'])
        unidad = self._unidad(obra, datos['antes_de'])
        if datos.get('reubicar_previo_inicial'):
            self._reubicar_previo_inicial(obra, unidad)
        previo = crear_previo(unidad)
        if 'fecha' in datos and previo.fecha != _fecha(datos['fecha']):
            previo.fecha = _fecha(datos['fecha'])
            previo.save(update_fields=['fecha'])
        self.stdout.write(f'Previo: {obra.titulo} · {previo.nombre} (frontera en la posición {previo.orden_frontera})')

    def _reubicar_previo_inicial(self, obra, unidad):
        """El previo de una obra aprobada sin estructura pasa a ser el de la entrega anunciada.
        Sus publicaciones lo acompañan y sus fronteras se recalculan al reordenar."""
        inicial = obra.unidades.filter(tipo=PREVIO, padre__isnull=True, orden_local=0).first()
        destino = obra.unidades.filter(tipo=PREVIO, padre_id=unidad.padre_id, orden_local=unidad.orden_local)
        if inicial is None or destino.exists():
            return
        inicial.padre = unidad.padre
        inicial.orden_local = unidad.orden_local
        inicial.nombre = f'Previo · {unidad.nombre}'
        inicial.save(update_fields=['padre', 'orden_local', 'nombre'])
        obra.recalcular_orden()

    def _progreso(self, datos):
        usuario = self._usuario(datos['usuario'])
        obra = self._obra_por_slug(datos['obra'])
        unidad = self._posicion(obra, datos)
        ProgresoUsuario.objects.update_or_create(
            usuario=usuario, obra=obra,
            defaults={'unidad_actual': unidad, 'orden_absoluto': calcular_orden_absoluto(unidad)},
        )
        self.stdout.write(f'Progreso: {usuario.username} · {obra.titulo} → {unidad.nombre}')

    def _publicacion(self, datos, rehacer):
        autor = self._usuario(datos['autor'])
        obra = self._obra_por_slug(datos['obra'])
        texto = datos['texto']
        existentes = Post.objects.filter(author=autor, obra=obra, text=texto)
        if existentes.exists():
            if not rehacer:
                self.existentes += 1
                return
            existentes.delete()

        frontera = self._posicion(obra, datos['frontera'])
        post = Post(
            author=autor, obra=obra, text=texto,
            referencia_narrativa=frontera, frontera_spoiler=frontera,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            emocion_autor=datos.get('emocion'),
        )
        cruzada = datos.get('cruzada')
        if cruzada:
            obra_cruzada = self._obra_por_slug(cruzada['obra'])
            post.obra_cruzada = obra_cruzada
            post.frontera_cruzada = self._unidad(obra_cruzada, cruzada['frontera'])
            post.modo_cruce = cruzada.get('modo', Post.MODO_COMPARATIVA)

        try:
            if datos.get('video'):
                aplicar_video(post, resolver_video(datos['video']))
            if datos.get('imagen'):
                archivo = descargar_imagen(datos['imagen'])
                extension = archivo.name.rsplit('.', 1)[-1]
                archivo.name = f'demo-{slugify(texto)[:40]}.{extension}'
                post.image = archivo
            post.full_clean()
        except (VideoNoValido, ValidationError) as exc:
            mensaje = exc.messages[0] if isinstance(exc, ValidationError) else str(exc)
            self._avisar(f'«{texto[:50]}»: {mensaje}')
            return
        post.save()
        self.creadas += 1
        self.stdout.write(f'Publicación: «{texto[:50]}»')

    def _avisar(self, mensaje):
        self.avisos += 1
        self.stderr.write(self.style.WARNING(mensaje))