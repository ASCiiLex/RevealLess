from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import EtapaPersonaje, Obra, Personaje, ProgresoUsuario, UnidadNarrativa
from narrative.services.personajes import presentacion_personaje
from subscriptions.services import crear_suscripcion


def _unidades(obra, total):
    unidades = [
        UnidadNarrativa.objects.create(obra=obra, tipo='episodio', nombre=f'E{i}', orden_local=i)
        for i in range(1, total + 1)
    ]
    obra.recalcular_orden()
    for unidad in unidades:
        unidad.refresh_from_db()
    return unidades


class EtapasPersonajeTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('lectora', password='x')
        self.client.force_login(self.usuario)
        self.serie = Obra.objects.create(titulo='Serie', slug='serie')
        self.otra = Obra.objects.create(titulo='Otra', slug='otra')
        self.e1, self.e2, self.e3 = _unidades(self.serie, 3)
        (self.o1,) = _unidades(self.otra, 1)

        self.personaje = Personaje.objects.create(nombre='Chico del sombrero')
        self.personaje.unidades.add(self.e1)
        EtapaPersonaje.objects.create(personaje=self.personaje, visible_tras=self.e2, alias='Capitán', nota='Recompensa: 30M')
        EtapaPersonaje.objects.create(personaje=self.personaje, visible_tras=self.e3, nota='Recompensa: 100M')

    def _progreso(self, unidad):
        ProgresoUsuario.objects.update_or_create(
            usuario=self.usuario, obra=unidad.obra,
            defaults={'unidad_actual': unidad, 'orden_absoluto': unidad.orden_fin},
        )

    def _presentacion(self, obra_id=None):
        progreso = dict(ProgresoUsuario.objects.filter(usuario=self.usuario).values_list('obra_id', 'orden_absoluto'))
        return presentacion_personaje(self.personaje, progreso, obra_id=obra_id)

    def test_sin_superar_ninguna_etapa_muestra_la_base(self):
        self._progreso(self.e1)
        datos = self._presentacion()
        self.assertEqual(datos['nombre'], 'Chico del sombrero')
        self.assertIsNone(datos['nota'])

    def test_etapa_superada_cambia_nombre_y_nota(self):
        self._progreso(self.e2)
        self.assertEqual(self._presentacion(), {
            'nombre': 'Capitán', 'imagen_url': '/static/img/default_personaje.jpg', 'nota': 'Recompensa: 30M',
        })

    def test_los_campos_vacios_heredan_de_la_etapa_anterior(self):
        self._progreso(self.e3)
        datos = self._presentacion()
        self.assertEqual((datos['nombre'], datos['nota']), ('Capitán', 'Recompensa: 100M'))

    def test_en_una_obra_no_cuentan_las_etapas_de_otra(self):
        EtapaPersonaje.objects.create(personaje=self.personaje, visible_tras=self.o1, alias='Alias de la otra obra')
        self._progreso(self.e1)
        self._progreso(self.o1)
        self.assertEqual(self._presentacion(obra_id=self.serie.id)['nombre'], 'Chico del sombrero')
        self.assertEqual(self._presentacion()['nombre'], 'Alias de la otra obra')

    def test_la_landing_de_obra_muestra_el_alias_sin_revelar_etapas_futuras(self):
        self._progreso(self.e2)
        datos = self.client.get(reverse('narrative_api_obra_landing', args=[self.serie.slug])).json()
        self.assertEqual(datos['personajes'][0]['nombre'], 'Capitán')
        self.assertEqual(datos['personajes'][0]['nota'], 'Recompensa: 30M')

    def test_las_suscripciones_usan_la_etapa_superada(self):
        self._progreso(self.e2)
        crear_suscripcion(self.usuario, personaje=self.personaje)
        datos = self.client.get(reverse('subscriptions_api_list')).json()
        self.assertEqual(datos[0]['personaje']['nombre'], 'Capitán')