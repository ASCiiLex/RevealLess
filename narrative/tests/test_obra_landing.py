from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, Personaje, RelevanciaPersonaje, UnidadNarrativa, TemaTransversal
from narrative.services import actualizar_progreso
from posts.models import Post
from subscriptions.services import crear_suscripcion


class ObraLandingAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('landing_user', password='x')
        self.otro_usuario = User.objects.create_user('landing_otro', password='x')

        self.obra = Obra.objects.create(
            titulo='Serie Landing', slug='serie-landing', sinopsis='Una sinopsis de prueba',
        )
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema Landing')

    def _nombres_personajes(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        return [p['nombre'] for p in response.data['personajes']]

    def _personajes_ana_y_bruno(self):
        ana = Personaje.objects.create(nombre='Ana')
        bruno = Personaje.objects.create(nombre='Bruno')
        ana.unidades.add(self.e1)
        bruno.unidades.add(self.e1, self.e2)
        return ana, bruno

    def _post_sobre(self, personaje, frontera):
        post = Post.objects.create(
            author=self.otro_usuario, obra=self.obra, text='x',
            referencia_narrativa=self.e1, frontera_spoiler=frontera, frontera_origen='explicito',
        )
        post.personajes.add(personaje)
        return post

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertEqual(response.status_code, 403)

    def test_devuelve_404_si_la_obra_no_existe(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=['no-existe']))
        self.assertEqual(response.status_code, 404)

    def test_incluye_sinopsis(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertEqual(response.data['sinopsis'], 'Una sinopsis de prueba')

    def test_progreso_pct_none_sin_progreso(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertIsNone(response.data['progreso_pct'])

    def test_progreso_pct_calculado_con_progreso(self):
        actualizar_progreso(self.usuario, self.obra, self.e2)
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertEqual(response.data['progreso_pct'], 100)

    def test_total_suscriptores_cuenta_usuarios_distintos(self):
        crear_suscripcion(self.usuario, self.obra)
        crear_suscripcion(self.otro_usuario, self.obra, tema=self.tema)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertEqual(response.data['total_suscriptores'], 2)

    def test_incluye_temas_con_estado_de_suscripcion(self):
        crear_suscripcion(self.usuario, self.obra, tema=self.tema)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        tema_data = response.data['temas'][0]
        self.assertEqual(tema_data['nombre'], 'Tema Landing')
        self.assertTrue(tema_data['suscrito'])
        self.assertIsNotNone(tema_data['suscripcion_id'])

    def test_suscrito_false_sin_suscripcion_de_obra(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertFalse(response.data['suscrito'])

    def test_progreso_pct_no_redondea_hacia_arriba_al_100_si_falta_algo(self):
        """Caso real detectado: 1160 de 1163 (99.74%) no debe mostrarse
        como 100% -- mostrar completo cuando de verdad quedan episodios
        pendientes contradice el proposito anti-spoiler."""
        obra_larga = Obra.objects.create(titulo='Obra larga', slug='obra-larga')
        unidades = [
            UnidadNarrativa.objects.create(
                obra=obra_larga, tipo='episodio', nombre=f'E{i}', orden_local=i,
            )
            for i in range(1, 1164)
        ]
        obra_larga.recalcular_orden()
        penultima = unidades[1159]
        penultima.refresh_from_db()
        actualizar_progreso(self.usuario, obra_larga, penultima)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[obra_larga.slug]))
        self.assertLess(response.data['progreso_pct'], 100)

    def test_progreso_pct_muestra_100_si_es_exactamente_completo(self):
        actualizar_progreso(self.usuario, self.obra, self.e2)
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertEqual(response.data['progreso_pct'], 100)

    def test_personajes_ordenados_por_apariciones_ya_vistas(self):
        self._personajes_ana_y_bruno()
        actualizar_progreso(self.usuario, self.obra, self.e2)
        self.assertEqual(self._nombres_personajes(), ['Bruno', 'Ana'])

    def test_apariciones_futuras_no_cuentan_para_el_orden(self):
        self._personajes_ana_y_bruno()
        actualizar_progreso(self.usuario, self.obra, self.e1)
        # Empate en apariciones vistas y primera aparición: desempata el nombre.
        self.assertEqual(self._nombres_personajes(), ['Ana', 'Bruno'])

    def test_la_relevancia_manual_prevalece_sobre_las_apariciones(self):
        ana, _ = self._personajes_ana_y_bruno()
        RelevanciaPersonaje.objects.create(
            personaje=ana, obra=self.obra, nivel=RelevanciaPersonaje.NIVEL_PROTAGONISTA,
        )
        actualizar_progreso(self.usuario, self.obra, self.e2)
        self.assertEqual(self._nombres_personajes(), ['Ana', 'Bruno'])

    def test_un_post_visible_pesa_mas_que_una_aparicion(self):
        ana, _ = self._personajes_ana_y_bruno()
        actualizar_progreso(self.usuario, self.obra, self.e2)
        self._post_sobre(ana, frontera=self.e1)
        # Ana: 2×1 post + 1 aparición = 3; Bruno: 2 apariciones.
        self.assertEqual(self._nombres_personajes(), ['Ana', 'Bruno'])

    def test_los_posts_no_visibles_no_cuentan(self):
        zoe = Personaje.objects.create(nombre='Zoe')
        bruno = Personaje.objects.create(nombre='Bruno')
        zoe.unidades.add(self.e1)
        bruno.unidades.add(self.e1)
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self._post_sobre(zoe, frontera=self.e2)
        self.assertEqual(self._nombres_personajes(), ['Bruno', 'Zoe'])