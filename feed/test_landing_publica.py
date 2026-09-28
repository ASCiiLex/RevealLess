import pytest
from django.urls import reverse

from narrative.models import Obra

pytestmark = pytest.mark.django_db


def _crear_obras(n):
    return [Obra.objects.create(titulo=f'Obra {i}', slug=f'obra-{i}') for i in range(n)]


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


def test_catalogo_publico_lista_todas_las_obras(client):
    _crear_obras(8)
    response = client.get(reverse('catalogo_publico'))

    assert response.status_code == 200
    assert len(response.context['obras']) == 8