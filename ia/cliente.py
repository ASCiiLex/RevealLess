"""Único punto de llamada a la API de Anthropic: cada llamada queda registrada en UsoIA."""

import logging
import os
import time
from decimal import Decimal

from django.conf import settings

logger = logging.getLogger(__name__)

# USD por millón de tokens, por prefijo de modelo: (entrada, salida) o (entrada, salida, lectura de caché).
# Sin lectura explícita se aplica FACTOR_CACHE_LECTURA. settings.IA_PRECIOS lo amplía o sustituye.
# Comprobar en https://platform.claude.com/docs/en/about-claude/pricing al cambiar de modelo.
PRECIOS_POR_DEFECTO = {
    'claude-haiku-4-5': (Decimal('1.00'), Decimal('5.00')),
    # Sonnet 5.5 cobra la lectura de caché a 0,05 veces la entrada, no a 0,1.
    'claude-sonnet-5-5': (Decimal('2.00'), Decimal('10.00'), Decimal('0.10')),
}
# Caché de 5 minutos: escribir cuesta 1,25 veces la entrada; leer, por defecto, una décima parte.
FACTOR_CACHE_ESCRITURA = Decimal('1.25')
FACTOR_CACHE_LECTURA = Decimal('0.1')
MILLON = Decimal(1_000_000)


class IANoConfigurada(RuntimeError):
    pass


def _precios():
    return {**PRECIOS_POR_DEFECTO, **getattr(settings, 'IA_PRECIOS', {})}


def coste_estimado(modelo, tokens_entrada, tokens_salida, cache_escritura=0, cache_lectura=0):
    """Coste en USD, o None si el modelo no tiene precio configurado (se guardan igual los tokens)."""
    for prefijo, precios in _precios().items():
        if modelo.startswith(prefijo):
            entrada, salida, *resto = (Decimal(str(p)) for p in precios)
            lectura = resto[0] if resto else entrada * FACTOR_CACHE_LECTURA
            total = (
                Decimal(tokens_entrada) * entrada
                + Decimal(cache_escritura) * entrada * FACTOR_CACHE_ESCRITURA
                + Decimal(cache_lectura) * lectura
                + Decimal(tokens_salida) * salida
            )
            return total / MILLON
    return None


def _entero(valor):
    return valor if isinstance(valor, int) and valor >= 0 else 0


def _registrar(**datos):
    """El registro nunca rompe la llamada que mide."""
    try:
        from .models import UsoIA
        UsoIA.objects.create(**datos)
    except Exception:
        logger.exception('No se pudo registrar el uso de IA')


def llamar_claude(funcion, *, usuario=None, obra=None, timeout=60, **parametros):
    """Hace messages.create con los parámetros recibidos y registra tokens, coste y duración,
    también si la llamada falla. Devuelve la respuesta tal cual; los errores de la API se propagan."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise IANoConfigurada('ANTHROPIC_API_KEY no configurada.')

    import anthropic

    modelo = parametros['model']
    inicio = time.monotonic()
    respuesta = None
    try:
        respuesta = anthropic.Anthropic(api_key=api_key, timeout=timeout).messages.create(**parametros)
        return respuesta
    finally:
        uso = getattr(respuesta, 'usage', None)
        entrada = _entero(getattr(uso, 'input_tokens', 0))
        salida = _entero(getattr(uso, 'output_tokens', 0))
        escritura = _entero(getattr(uso, 'cache_creation_input_tokens', 0))
        lectura = _entero(getattr(uso, 'cache_read_input_tokens', 0))
        _registrar(
            funcion=funcion,
            modelo=modelo,
            usuario=usuario if getattr(usuario, 'is_authenticated', False) else None,
            obra=obra,
            tokens_entrada=entrada,
            tokens_cache_escritura=escritura,
            tokens_cache_lectura=lectura,
            tokens_salida=salida,
            coste_estimado=coste_estimado(modelo, entrada, salida, escritura, lectura),
            exito=respuesta is not None,
            duracion_ms=int((time.monotonic() - inicio) * 1000),
        )