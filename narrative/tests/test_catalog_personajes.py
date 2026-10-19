from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import EtapaPersonaje, Personaje, TemaTransversal
from narrative.services import actualizar_progreso
from posts.tests.utils import crear_obra
from subscriptions.models import Suscripcion
from subscriptions.services import crear_suscripcion


class LomosPersonajeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_lomos_pj', password='x')
        self.obra, (self.e1, self.e2) = crear_obra('lomos-personaje', n=2)
        actualizar_progreso(self.usuario, self.obra, self.e1)

        self.conocido = Personaje.objects.create(nombre='Conocido')
        self.conocido.unidades.add(self.e1)
        self.futuro = Personaje.objects.create(nombre='Futuro')
        self.futuro.unidades.add(self.e2)

        self.suscripcion = crear_suscripcion(self.usuario, personaje=self.conocido)
        crear_suscripcion(self.usuario, personaje=self.futuro)
        self.client.force_authenticate(user=self.usuario)

    def _biblioteca(self):
        return self.client.get(reverse('narrative_api_obras')).data['biblioteca']

    def _lomos_personaje(self):
        return [o for o in self._biblioteca() if o.get('es_personaje')]

    def test_solo_lista_personajes_ya_alcanzados(self):
        self.assertEqual([o['personaje_id'] for o in self._lomos_personaje()], [self.conocido.id])

    def test_formato_del_lomo(self):
        (lomo,) = self._lomos_personaje()
        self.assertEqual(lomo['clave'], f'personaje-{self.conocido.id}')
        self.assertEqual(lomo['titulo'], 'Conocido')
        self.assertEqual(lomo['categorias'], ['Personajes'])
        self.assertEqual(lomo['suscripcion_id'], self.suscripcion.id)
        self.assertTrue(lomo['suscrito'])
        self.assertFalse(lomo['silenciada'])

    def test_muestra_el_alias_de_una_etapa_superada(self):
        EtapaPersonaje.objects.create(personaje=self.conocido, visible_tras=self.e1, alias='Alias revelado')
        (lomo,) = self._lomos_personaje()
        self.assertEqual(lomo['titulo'], 'Alias revelado')

    def test_no_revela_el_alias_de_una_etapa_futura(self):
        EtapaPersonaje.objects.create(personaje=self.conocido, visible_tras=self.e2, alias='Secreto')
        (lomo,) = self._lomos_personaje()
        self.assertEqual(lomo['titulo'], 'Conocido')

    def test_lomo_silenciado(self):
        Suscripcion.objects.filter(pk=self.suscripcion.pk).update(activa=False)
        (lomo,) = self._lomos_personaje()
        self.assertTrue(lomo['silenciada'])

    def test_las_claves_no_se_repiten_entre_tipos(self):
        tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema')
        crear_suscripcion(self.usuario, self.obra, tema=tema)
        crear_suscripcion(self.usuario, self.obra)

        claves = [o['clave'] for o in self._biblioteca()]
        self.assertEqual(len(claves), len(set(claves)))
        self.assertIn(f'obra-{self.obra.id}', claves)
        self.assertIn(f'tema-{tema.id}', claves)
        self.assertIn(f'personaje-{self.conocido.id}', claves)