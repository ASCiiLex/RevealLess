from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import EtapaPersonaje, Obra, Personaje, RelevanciaPersonaje, UnidadNarrativa, TemaTransversal
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

    def _landing(self):
        self.client.force_authenticate(user=self.usuario)
        return self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug])).data

    def _nombres_personajes(self):
        return [p['nombre'] for p in self._landing()['personajes']]

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

    def _relevancia(self, personaje, nivel):
        RelevanciaPersonaje.objects.create(personaje=personaje, obra=self.obra, nivel=nivel)

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertEqual(response.status_code, 403)

    def test_devuelve_404_si_la_obra_no_existe(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=['no-existe']))
        self.assertEqual(response.status_code, 404)

    def test_incluye_sinopsis(self):
        self.assertEqual(self._landing()['sinopsis'], 'Una sinopsis de prueba')

    def test_progreso_pct_none_sin_progreso(self):
        self.assertIsNone(self._landing()['progreso_pct'])

    def test_progreso_pct_calculado_con_progreso(self):
        actualizar_progreso(self.usuario, self.obra, self.e2)
        self.assertEqual(self._landing()['progreso_pct'], 100)

    def test_total_suscriptores_cuenta_usuarios_distintos(self):
        crear_suscripcion(self.usuario, self.obra)
        crear_suscripcion(self.otro_usuario, self.obra, tema=self.tema)
        self.assertEqual(self._landing()['total_suscriptores'], 2)

    def test_incluye_temas_con_estado_de_suscripcion(self):
        crear_suscripcion(self.usuario, self.obra, tema=self.tema)
        tema_data = self._landing()['temas'][0]
        self.assertEqual(tema_data['nombre'], 'Tema Landing')
        self.assertTrue(tema_data['suscrito'])
        self.assertIsNotNone(tema_data['suscripcion_id'])

    def test_suscrito_false_sin_suscripcion_de_obra(self):
        self.assertFalse(self._landing()['suscrito'])

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
        self.assertEqual(self._landing()['progreso_pct'], 100)

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
        self._relevancia(ana, RelevanciaPersonaje.NIVEL_PROTAGONISTA)
        actualizar_progreso(self.usuario, self.obra, self.e2)
        self.assertEqual(self._nombres_personajes(), ['Ana', 'Bruno'])

    def test_episodico_queda_por_detras_de_los_sin_marcar(self):
        ana, _ = self._personajes_ana_y_bruno()
        self._relevancia(ana, RelevanciaPersonaje.NIVEL_EPISODICO)
        actualizar_progreso(self.usuario, self.obra, self.e1)
        # Sin relevancia, Ana iría primero por nombre.
        self.assertEqual(self._nombres_personajes(), ['Bruno', 'Ana'])

    def test_sin_marcar_equivale_a_secundario(self):
        ana, _ = self._personajes_ana_y_bruno()
        self._relevancia(ana, RelevanciaPersonaje.NIVEL_SECUNDARIO)
        actualizar_progreso(self.usuario, self.obra, self.e2)
        # Mismo nivel: decide el peso (Bruno tiene dos apariciones vistas).
        self.assertEqual(self._nombres_personajes(), ['Bruno', 'Ana'])

    def test_principales_en_orden_de_presentacion(self):
        zoro = Personaje.objects.create(nombre='Zoro')
        robin = Personaje.objects.create(nombre='Robin')
        zoro.unidades.add(self.e1)
        robin.unidades.add(self.e2)
        self._relevancia(zoro, RelevanciaPersonaje.NIVEL_PRINCIPAL)
        self._relevancia(robin, RelevanciaPersonaje.NIVEL_PRINCIPAL)
        actualizar_progreso(self.usuario, self.obra, self.e2)
        self._post_sobre(robin, frontera=self.e1)
        # Robin pesa más (post + aparición), pero Zoro se presentó antes.
        self.assertEqual(self._nombres_personajes(), ['Zoro', 'Robin'])

    def test_una_etapa_superada_cambia_el_nivel(self):
        ana, bruno = Personaje.objects.create(nombre='Ana'), Personaje.objects.create(nombre='Bruno')
        ana.unidades.add(self.e1)
        bruno.unidades.add(self.e1)
        self._relevancia(ana, RelevanciaPersonaje.NIVEL_EPISODICO)
        EtapaPersonaje.objects.create(personaje=ana, visible_tras=self.e2, nivel=RelevanciaPersonaje.NIVEL_PROTAGONISTA)

        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.assertEqual(self._nombres_personajes(), ['Bruno', 'Ana'])

        actualizar_progreso(self.usuario, self.obra, self.e2)
        datos = {p['nombre']: p['nivel'] for p in self._landing()['personajes']}
        self.assertEqual(self._nombres_personajes(), ['Ana', 'Bruno'])
        self.assertEqual(datos['Ana'], RelevanciaPersonaje.NIVEL_PROTAGONISTA)

    def test_cada_personaje_incluye_su_nivel(self):
        ana, _ = self._personajes_ana_y_bruno()
        self._relevancia(ana, RelevanciaPersonaje.NIVEL_PRINCIPAL)
        actualizar_progreso(self.usuario, self.obra, self.e1)
        niveles = {p['nombre']: p['nivel'] for p in self._landing()['personajes']}
        self.assertEqual(niveles, {
            'Ana': RelevanciaPersonaje.NIVEL_PRINCIPAL,
            'Bruno': RelevanciaPersonaje.NIVEL_SIN_MARCAR,
        })

    def test_grupos_de_relevancia_cubren_los_cinco_niveles(self):
        grupos = self._landing()['grupos_relevancia']
        self.assertEqual([g['clave'] for g in grupos], ['principales', 'destacados', 'secundarios'])
        self.assertEqual([g['clave'] for g in grupos if g['por_defecto']], ['principales'])
        niveles = sorted(n for g in grupos for n in g['niveles'])
        self.assertEqual(niveles, sorted(valor for valor, _ in RelevanciaPersonaje.NIVEL_CHOICES))

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