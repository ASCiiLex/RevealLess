import logging
import time

from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class RegistroLentitudMiddleware:
    """Registra las peticiones que superan RENDIMIENTO_UMBRAL_MS con su nº de consultas y el tiempo
    pasado en la base de datos: separa la lentitud de Postgres de la del propio Django."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        consultas = {'n': 0, 'segundos': 0.0}

        def medir(execute, sql, params, many, context):
            inicio = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                consultas['n'] += 1
                consultas['segundos'] += time.perf_counter() - inicio

        inicio = time.perf_counter()
        with connection.execute_wrapper(medir):
            response = self.get_response(request)
        total_ms = (time.perf_counter() - inicio) * 1000

        if total_ms >= settings.RENDIMIENTO_UMBRAL_MS:
            logger.warning(
                'Lenta: %s %s -> %s | %.0f ms | %d consultas | %.0f ms en BD',
                request.method, request.get_full_path(), response.status_code,
                total_ms, consultas['n'], consultas['segundos'] * 1000,
            )
        return response