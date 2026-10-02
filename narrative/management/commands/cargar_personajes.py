import re
import unicodedata
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from narrative.models import (
    EtapaPersonaje, Obra, Personaje, PropuestaAparicion, RelevanciaPersonaje, UnidadNarrativa,
)
from narrative.services.personajes import aprobar_propuesta

R = RelevanciaPersonaje
NIVELES = {
    'protagonista': R.NIVEL_PROTAGONISTA,
    'principal': R.NIVEL_PRINCIPAL,
    'destacado': R.NIVEL_DESTACADO,
    'secundario': R.NIVEL_SECUNDARIO,
    'episodico': R.NIVEL_EPISODICO,
}


def _nivel(valor):
    if isinstance(valor, int):
        return valor
    return NIVELES[str(valor).lower().replace('ó', 'o')]


def normalizar(texto):
    """Clave para comparar nombres: sin aclaraciones entre paréntesis, tildes ni macrones (Hyūga = Hyuga)."""
    texto = re.sub(r'\([^)]*\)', ' ', texto)
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c)).lower()
    return ' '.join(re.findall(r'\w+', texto))


class Command(BaseCommand):
    help = ('Carga datos editoriales de personajes desde un YAML: personajes nuevos, relevancia por obra, '
            'apariciones manuales aprobadas y etapas (alias, nota, nivel). Solo escribe lo que trae el '
            'fichero: las imágenes ya subidas se conservan.')

    def add_arguments(self, parser):
        parser.add_argument('fichero')
        parser.add_argument('--dry-run', action='store_true', help='Ejecuta todo y lo deshace al final.')

    def handle(self, *args, **opciones):
        ruta = Path(opciones['fichero'])
        if not ruta.exists():
            raise CommandError(f'No existe {ruta}')
        datos = yaml.safe_load(ruta.read_text(encoding='utf-8'))

        self.tipo = datos.get('tipo_unidad', 'arco')
        # exacta: títulos completos (películas); regex: patrones (arcos con nombres variables).
        self.exacta = datos.get('coincidencia', 'regex') == 'exacta'
        self.avisos = 0
        self._cache = None
        self.obras = list(Obra.objects.filter(slug__in=datos['obras']))
        for slug in set(datos['obras']) - {o.slug for o in self.obras}:
            self._aviso(f'Obra no encontrada: {slug}')

        with transaction.atomic():
            self._nuevos(datos.get('nuevos', []))
            self._relevancias(datos.get('relevancias', []))
            self._apariciones(datos.get('apariciones', []))
            self._etapas(datos.get('etapas', []))
            if opciones['dry_run']:
                transaction.set_rollback(True)

        prefijo = '[dry-run, sin guardar] ' if opciones['dry_run'] else ''
        estilo = self.style.SUCCESS if not self.avisos else self.style.WARNING
        self.stdout.write(estilo(f'{prefijo}Terminado con {self.avisos} aviso(s).'))

    def _aviso(self, texto):
        self.avisos += 1
        self.stdout.write(self.style.WARNING(texto))

    def _indice(self):
        """Nombre normalizado → id; primero nombres, después alias de etapas."""
        if self._cache is None:
            self._cache = {}
            for pid, nombre in Personaje.objects.order_by('id').values_list('id', 'nombre'):
                self._cache.setdefault(normalizar(nombre), pid)
            for pid, alias in EtapaPersonaje.objects.exclude(alias='').values_list('personaje_id', 'alias'):
                self._cache.setdefault(normalizar(alias), pid)
        return self._cache

    def _personaje(self, referencia):
        if isinstance(referencia, int):
            personaje = Personaje.objects.filter(id=referencia).first()
        else:
            pid = self._indice().get(normalizar(referencia))
            personaje = Personaje.objects.filter(id=pid).first() if pid else None
        if personaje is None:
            self._aviso(f'Personaje no encontrado: {referencia}')
        return personaje

    def _unidad(self, obra, referencia):
        if isinstance(referencia, int):
            unidad = UnidadNarrativa.objects.filter(obra=obra, id=referencia).first()
        else:
            filtro = {'nombre__iexact': referencia} if self.exacta else {'nombre__iregex': referencia}
            unidad = (
                UnidadNarrativa.objects.filter(obra=obra, tipo=self.tipo, **filtro)
                .order_by('orden_fin').last()
            )
        if unidad is None:
            self._aviso(f'  [{obra.slug}] sin unidad «{referencia}»')
        return unidad

    def _nuevos(self, nombres):
        for nombre in nombres:
            clave = normalizar(nombre)
            if clave in self._indice():
                continue
            personaje = Personaje.objects.create(nombre=nombre)
            self._indice()[clave] = personaje.id
            self.stdout.write(f'Nuevo personaje: {nombre}')

    def _relevancias(self, entradas):
        for entrada in entradas:
            personaje = self._personaje(entrada['personaje'])
            if personaje is None:
                continue
            nivel = _nivel(entrada['nivel'])
            for obra in self.obras:
                R.objects.update_or_create(personaje=personaje, obra=obra, defaults={'nivel': nivel})
            self.stdout.write(f'Relevancia {personaje.nombre}: {dict(R.NIVEL_CHOICES)[nivel]}')

    def _apariciones(self, entradas):
        for entrada in entradas:
            personaje = self._personaje(entrada['personaje'])
            if personaje is None:
                continue
            for obra in self.obras:
                nuevas = 0
                for referencia in entrada['unidades']:
                    unidad = self._unidad(obra, referencia)
                    if unidad is None:
                        continue
                    propuesta, _ = PropuestaAparicion.objects.get_or_create(
                        personaje=personaje, unidad=unidad,
                        defaults={'origen': PropuestaAparicion.ORIGEN_MANUAL},
                    )
                    if propuesta.estado != PropuestaAparicion.ESTADO_APROBADA:
                        aprobar_propuesta(propuesta)
                        nuevas += 1
                self.stdout.write(f'  [{obra.slug}] {personaje.nombre}: {nuevas} aparición(es) añadida(s)')

    def _etapas(self, entradas):
        for entrada in entradas:
            personaje = self._personaje(entrada['personaje'])
            if personaje is None:
                continue
            campos = {c: entrada[c] for c in ('alias', 'nota') if c in entrada}
            if 'nivel' in entrada:
                campos['nivel'] = _nivel(entrada['nivel'])
            for obra in self.obras:
                unidad = self._unidad(obra, entrada['tras'])
                if unidad is None:
                    continue
                EtapaPersonaje.objects.update_or_create(personaje=personaje, visible_tras=unidad, defaults=campos)
                self.stdout.write(f'  [{obra.slug}] {personaje.nombre} tras {unidad.nombre}: {campos}')