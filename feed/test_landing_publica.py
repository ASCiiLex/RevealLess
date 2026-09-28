import pytest
from django.urls import reverse

from narrative.models import Obra

pytestmark = pytest.mark.django_db


def _crear_obras(n):
    return [Obra.objects.create(titulo=f'Obra {i:02d}', slug=f'obra-{i}') for i in range(n)]


def _nombres_plantillas(response):
    return [t.name for t in response.templates]


def test_landing_anonima_limita_el_adelanto_a_seis_obras(client):
    _crear_obras(8)
    response = client.get(reverse('feed_publico'))

    assert response.status_code == 200
    assert len(response.context['obras']) == 6
    assert response.context['stats']['obras_count'] == 8


def test_landing_redirige_al_feed_con_sesion(client, django_user_model):
    user = django_user_model.objects.create_user(username='lector', password='x')
    client.force_login(user)

    response = client.get(reverse('feed_publico'))

    assert response.status_code == 302
    assert response.url == reverse('feed')


def test_catalogo_publico_muestra_la_primera_tanda(client):
    _crear_obras(14)
    response = client.get(reverse('catalogo_publico'))

    assert response.status_code == 200
    assert response.context['total_obras'] == 14
    assert len(response.context['pagina']) == 12
    assert response.context['pagina'].has_next()


def test_catalogo_parcial_devuelve_solo_tarjetas_y_la_pagina_siguiente(client):
    _crear_obras(14)
    response = client.get(reverse('catalogo_publico'), {'pagina': 2, 'parcial': 1})

    assert response.status_code == 200
    assert _nombres_plantillas(response) == ['feed/_catalogo_tarjetas.html']
    assert len(response.context['pagina']) == 2
    assert response['X-Pagina-Siguiente'] == ''


def test_catalogo_parcial_indica_la_siguiente_si_quedan_obras(client):
    _crear_obras(30)
    response = client.get(reverse('catalogo_publico'), {'pagina': 1, 'parcial': 1})

    assert response['X-Pagina-Siguiente'] == '2'


def test_catalogo_pagina_no_numerica_cae_en_la_primera(client):
    _crear_obras(3)
    response = client.get(reverse('catalogo_publico'), {'pagina': 'abc'})

    assert response.status_code == 200
    assert response.context['pagina'].number == 1