import os
import time

import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum
from django.utils import timezone

from ia.models import UsoIA
from narrative.ai_assistant import MODELO_IA, TIMEOUT_SUGERENCIA, etiqueta_unidad, proponer_clasificacion
from narrative.models import Obra, UnidadNarrativa

SEPARADOR_PADRE = ' · '


class CasoInvalido(Exception):
    pass


class Command(BaseCommand):
    help = (
        'Mide la precisión de la IA de fronteras con casos de respuesta conocida. '
        'LLAMA A LA API REAL: cada caso y modelo es una llamada con coste.'
    )

    def add_arguments(self, parser):
        parser.add_argument('archivo', help='YAML de casos (ver narrative/data/evaluacion_fronteras.yaml).')
        parser.add_argument(
            '--modelo', action='append', default=[],
            help='Modelo a evaluar (repetible). Por defecto, el que usa la web.',
        )

    def handle(self, *args, **opciones):
        with open(opciones['archivo'], encoding='utf-8') as f:
            crudos = yaml.safe_load(f) or []

        casos = []
        for numero, crudo in enumerate(crudos, start=1):
            try:
                casos.append(self._caso(crudo))
            except CasoInvalido as e:
                self.stderr.write(self.style.WARNING(f'Caso {numero} omitido: {e}'))
        if not casos:
            raise CommandError('No hay casos válidos que evaluar.')

        modelos = opciones['modelo'] or [os.environ.get('ANTHROPIC_MODEL') or MODELO_IA]
        self.stdout.write(f'{len(casos)} caso(s) × {len(modelos)} modelo(s) = {len(casos) * len(modelos)} llamada(s).\n')
        for modelo in modelos:
            self._evaluar(modelo, casos)

    def _unidad(self, obra, valor):
        """Por id o por nombre; «Padre · Nombre» desambigua nombres repetidos."""
        texto = str(valor).strip()
        if texto.isdigit():
            unidades = UnidadNarrativa.objects.filter(obra=obra, id=int(texto))
        elif SEPARADOR_PADRE in texto:
            padre, nombre = texto.rsplit(SEPARADOR_PADRE, 1)
            unidades = UnidadNarrativa.objects.filter(obra=obra, nombre__iexact=nombre, padre__nombre__iexact=padre)
        else:
            unidades = UnidadNarrativa.objects.filter(obra=obra, nombre__iexact=texto)
        unidades = list(unidades.select_related('padre')[:2])
        if len(unidades) != 1:
            motivo = 'no existe' if not unidades else 'es ambigua (usa «Padre · Nombre» o el id)'
            raise CasoInvalido(f'la unidad «{texto}» {motivo} en {obra.titulo}.')
        return unidades[0]

    def _caso(self, crudo):
        try:
            obra = Obra.objects.get(slug=crudo['obra'])
        except (KeyError, TypeError):
            raise CasoInvalido('falta «obra».')
        except Obra.DoesNotExist:
            raise CasoInvalido(f'no existe la obra «{crudo["obra"]}».')
        if not crudo.get('texto') or not crudo.get('esperada'):
            raise CasoInvalido('faltan «texto» o «esperada».')
        return {
            'obra': obra,
            'texto': crudo['texto'],
            'referencia': self._unidad(obra, crudo['referencia']) if crudo.get('referencia') else None,
            'esperada': self._unidad(obra, crudo['esperada']),
        }

    def _evaluar(self, modelo, casos):
        self.stdout.write(self.style.MIGRATE_HEADING(f'\n== {modelo} =='))
        inicio = timezone.now()
        exactos = pronto = tarde = sin_respuesta = 0
        distancias, confianzas = [], []

        for numero, caso in enumerate(casos, start=1):
            antes = time.monotonic()
            sugerencia = proponer_clasificacion(
                caso['texto'], caso['obra'], caso['referencia'],
                timeout=TIMEOUT_SUGERENCIA, funcion=UsoIA.FUNCION_EVALUACION, modelo=modelo,
            )
            segundos = time.monotonic() - antes
            esperada = caso['esperada']
            propuesta = sugerencia.frontera_spoiler

            if propuesta is None:
                sin_respuesta += 1
                self.stdout.write(f'{numero:>3}  SIN RESPUESTA   esperada: {etiqueta_unidad(esperada)}')
                continue

            diferencia = propuesta.orden_frontera - esperada.orden_frontera
            confianzas.append(sugerencia.confianza)
            distancias.append(abs(diferencia))
            if diferencia == 0:
                exactos += 1
                marca = 'EXACTO'
            elif diferencia < 0:
                pronto += 1
                marca = 'PRONTO (fuga)'
            else:
                tarde += 1
                marca = 'TARDE'
            self.stdout.write(
                f'{numero:>3}  {marca:<14}  esperada: {etiqueta_unidad(esperada)}  '
                f'| propuesta: {etiqueta_unidad(propuesta)}  | dif: {diferencia:+d}  '
                f'| conf: {sugerencia.confianza:.2f}  | {segundos:.1f}s'
            )

        total = len(casos)
        uso = UsoIA.objects.filter(
            funcion=UsoIA.FUNCION_EVALUACION, modelo=modelo, creado_en__gte=inicio,
        ).aggregate(coste=Sum('coste_estimado'), entrada=Sum('tokens_entrada'), salida=Sum('tokens_salida'))
        coste = f'{uso["coste"]:.4f} USD' if uso['coste'] is not None else 'sin precio configurado'

        self.stdout.write(self.style.SUCCESS(f'Exactos: {exactos}/{total}'))
        self.stdout.write(self.style.ERROR(f'Demasiado pronto (fuga): {pronto}'))
        self.stdout.write(f'Demasiado tarde: {tarde}')
        self.stdout.write(f'Sin respuesta: {sin_respuesta}')
        if distancias:
            self.stdout.write(f'Distancia media: {sum(distancias) / len(distancias):.1f} posiciones')
            self.stdout.write(f'Confianza media: {sum(confianzas) / len(confianzas):.2f}')
        self.stdout.write(f'Tokens: {uso["entrada"] or 0} de entrada, {uso["salida"] or 0} de salida · Coste: {coste}')