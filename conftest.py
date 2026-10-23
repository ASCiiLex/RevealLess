import pytest


@pytest.fixture(autouse=True)
def sin_clave_de_ia(monkeypatch):
    """Ningún test llama a la API de Anthropic de verdad: los que necesitan IA la simulan."""
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)


def _transaccional(item):
    """Vacía las tablas al terminar: tiene que ir detrás de los demás, como ordena pytest-django."""
    from django.test import TestCase, TransactionTestCase

    clase = getattr(item, 'cls', None)
    if clase is not None and issubclass(clase, TransactionTestCase) and not issubclass(clase, TestCase):
        return True
    marca = item.get_closest_marker('django_db')
    if marca is None:
        return False
    transaccion = marca.kwargs.get('transaction', marca.args[0] if marca.args else False)
    return bool(transaccion or marca.kwargs.get('reset_sequences'))


@pytest.hookimpl(wrapper=True)
def pytest_collection_modifyitems(items):
    """pytest-django agrupa los tests por tipo (con base de datos, transaccionales, sin base de datos).
    Se recupera el orden de recogida, alfabético por app y archivo; solo los transaccionales van al final."""
    posicion = {item.nodeid: i for i, item in enumerate(items)}
    resultado = yield
    items.sort(key=lambda item: (_transaccional(item), posicion[item.nodeid]))
    return resultado