import logging
import time

from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class RegistroLentitudMiddleware:
    """Registra las peticiones que superan RENDIMIENTO_UMBRAL_MS con su nº de consultas, el tiempo
    en la base de datos y la consulta más lenta: separa la lentitud de Postgres de la del código."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        consultas = {'n': 0, 'segundos': 0.0, 'max': 0.0, 'sql': ''}

        def medir(execute, sql, params, many, context):
            inicio = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                duracion = time.perf_counter() - inicio
                consultas['n'] += 1
                consultas['segundos'] += duracion
                if duracion > consultas['max']:
                    consultas['max'] = duracion
                    # Solo el SQL, sin parámetros: nunca llegan datos de usuarios al log.
                    consultas['sql'] = ' '.join(sql.split())[:160]

        inicio = time.perf_counter()
        with connection.execute_wrapper(medir):
            response = self.get_response(request)
        total_ms = (time.perf_counter() - inicio) * 1000

        if total_ms >= settings.RENDIMIENTO_UMBRAL_MS:
            logger.warning(
                'Lenta: %s %s -> %s | %.0f ms | %d consultas | %.0f ms en BD | más lenta %.0f ms: %s',
                request.method, request.get_full_path(), response.status_code,
                total_ms, consultas['n'], consultas['segundos'] * 1000,
                consultas['max'] * 1000, consultas['sql'],
            )
        return response