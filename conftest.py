import pytest


@pytest.fixture(autouse=True)
def sin_clave_de_ia(monkeypatch):
    """Ningún test llama a la API de Anthropic de verdad: los que necesitan IA la simulan."""
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)