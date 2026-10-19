from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, TemaTransversal, UnidadNarrativa
from narrative.services import actualizar_progreso
from subscriptions.models import Suscripcion
from subscriptions.services import crear_suscripcion


class CatalogoObrasAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_catalogo', password='x')

        self.obra_con_progreso = Obra.objects.create(titulo='Con progreso', slug='con-progreso')
        self.obra_con_suscripcion = Obra.objects.create(titulo='Con suscripcion', slug='con-suscripcion')
        self.obra_sin_relacion = Obra.objects.create(titulo='Sin relacion', slug='sin-relacion')

        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra_con_progreso, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra_con_progreso.recalcular_orden()
        self.e1.refresh_from_db()

        actualizar_progreso(self.usuario, self.obra_con_progreso, self.e1)
        crear_suscripcion(self.usuario, self.obra_con_suscripcion)

    def _catalogo(self):
        self.client.force_authenticate(user=self.usuario)
        return self.client.get(reverse('narrative_api_obras')).data

    @staticmethod
    def _slugs(lista):
        return {o['slug'] for o in lista if not o.get('es_tema')}

    @staticmethod
    def _lomo(lista, slug):
        return next(o for o in lista if o['slug'] == slug and not o.get('es_tema'))

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('narrative_api_obras'))
        self.assertEqual(response.status_code, 403)

    def test_obra_con_progreso_va_a_biblioteca(self):
        self.assertIn('con-progreso', self._slugs(self._catalogo()['biblioteca']))

    def test_obra_con_suscripcion_va_a_biblioteca(self):
        self.assertIn('con-suscripcion', self._slugs(self._catalogo()['biblioteca']))

    def test_obra_sin_relacion_va_solo_a_descubrir(self):
        datos = self._catalogo()
        self.assertIn('sin-relacion', self._slugs(datos['descubrir']))
        self.assertNotIn('sin-relacion', self._slugs(datos['biblioteca']))

    def test_obra_con_progreso_sin_seguir_aparece_en_ambas(self):
        datos = self._catalogo()
        self.assertIn('con-progreso', self._slugs(datos['biblioteca']))
        self.assertIn('con-progreso', self._slugs(datos['descubrir']))

    def test_obra_seguida_entera_no_aparece_en_descubrir(self):
        self.assertNotIn('con-suscripcion', self._slugs(self._catalogo()['descubrir']))

    def test_obra_silenciada_queda_en_biblioteca_marcada_y_fuera_de_descubrir(self):
        Suscripcion.objects.filter(usuario=self.usuario, obra=self.obra_con_suscripcion).update(activa=False)
        datos = self._catalogo()
        lomo = self._lomo(datos['biblioteca'], 'con-suscripcion')
        self.assertTrue(lomo['silenciada'])
        self.assertTrue(lomo['suscrito'])
        self.assertNotIn('con-suscripcion', self._slugs(datos['descubrir']))

    def test_respuesta_incluye_imagen_url_categorias_y_silenciada(self):
        obra_data = self._catalogo()['biblioteca'][0]
        self.assertIn('imagen_url', obra_data)
        self.assertIn('categorias', obra_data)
        self.assertIn('silenciada', obra_data)

    def test_progreso_pct_en_ambas_estanterias(self):
        datos = self._catalogo()
        self.assertEqual(self._lomo(datos['biblioteca'], 'con-progreso')['progreso_pct'], 100)
        self.assertEqual(self._lomo(datos['descubrir'], 'con-progreso')['progreso_pct'], 100)

    def test_progreso_pct_es_none_sin_progreso_registrado(self):
        datos = self._catalogo()
        self.assertIsNone(self._lomo(datos['biblioteca'], 'con-suscripcion')['progreso_pct'])
        self.assertIsNone(self._lomo(datos['descubrir'], 'sin-relacion')['progreso_pct'])

    def test_suscrito_true_para_obra_con_suscripcion(self):
        self.assertTrue(self._lomo(self._catalogo()['biblioteca'], 'con-suscripcion')['suscrito'])

    def test_suscrito_false_para_obra_solo_con_progreso(self):
        self.assertFalse(self._lomo(self._catalogo()['biblioteca'], 'con-progreso')['suscrito'])

    def test_suscripcion_id_presente_para_suscripcion_de_obra_completa(self):
        self.assertIsNotNone(self._lomo(self._catalogo()['biblioteca'], 'con-suscripcion')['suscripcion_id'])

    def test_suscripcion_id_es_none_sin_ninguna_suscripcion(self):
        self.assertIsNone(self._lomo(self._catalogo()['biblioteca'], 'con-progreso')['suscripcion_id'])

    def test_suscripcion_de_nivel_fino_no_marca_la_obra_como_seguida(self):
        """Solo la suscripción a obra completa cuenta como «Siguiendo»: es la única que el
        botón del lomo puede deshacer. La obra entra en Biblioteca y sigue en Descubrir."""
        obra_solo_unidad = Obra.objects.create(titulo='Solo unidad', slug='solo-unidad')
        unidad = UnidadNarrativa.objects.create(
            obra=obra_solo_unidad, tipo='arco', nombre='Arco 1', orden_local=1,
        )
        crear_suscripcion(self.usuario, obra_solo_unidad, unidad=unidad)

        datos = self._catalogo()
        lomo = self._lomo(datos['biblioteca'], 'solo-unidad')
        self.assertFalse(lomo['suscrito'])
        self.assertIsNone(lomo['suscripcion_id'])
        self.assertIn('solo-unidad', self._slugs(datos['descubrir']))

    def test_lomo_de_tema_suscrito_y_silenciado(self):
        tema = TemaTransversal.objects.create(obra=self.obra_sin_relacion, nombre='Tema seguido')
        crear_suscripcion(self.usuario, self.obra_sin_relacion, tema=tema)

        lomo = next(o for o in self._catalogo()['biblioteca'] if o.get('es_tema'))
        self.assertEqual(lomo['tema_id'], tema.id)
        self.assertEqual(lomo['id'], -tema.id)
        self.assertFalse(lomo['silenciada'])

        Suscripcion.objects.filter(usuario=self.usuario, tema=tema).update(activa=False)
        lomo = next(o for o in self._catalogo()['biblioteca'] if o.get('es_tema'))
        self.assertTrue(lomo['silenciada'])