from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa
from narrative.serializers.obras import calcular_progreso_pct
from narrative.services import actualizar_progreso
from narrative.services.longitud import longitudes_principales


def crear_unidad(obra, tipo, nombre, orden_local):
    return UnidadNarrativa.objects.create(obra=obra, tipo=tipo, nombre=nombre, orden_local=orden_local)


class LongitudPrincipalTests(TestCase):
    """Anime con un previo y una película tras el último episodio (caso God Valley)."""

    def setUp(self):
        self.obra = Obra.objects.create(titulo='Anime longitud', slug='anime-longitud')
        self.e1 = crear_unidad(self.obra, 'episodio', 'Episodio 1', 1)
        self.e2 = crear_unidad(self.obra, 'episodio', 'Episodio 2', 2)
        self.previo = crear_unidad(self.obra, UnidadNarrativa.TIPO_PREVIO, 'Previo · Película', 3)
        self.pelicula = crear_unidad(self.obra, 'pelicula', 'Película', 4)
        self.obra.recalcular_orden()
        for unidad in (self.e1, self.e2, self.previo, self.pelicula):
            unidad.refresh_from_db()

    def test_cuenta_hasta_el_ultimo_episodio(self):
        self.assertEqual(longitudes_principales([self.obra.id]), {self.obra.id: self.e2.orden_fin})

    def test_al_dia_en_episodios_es_100(self):
        longitud = longitudes_principales([self.obra.id])[self.obra.id]
        self.assertEqual(calcular_progreso_pct(self.e2.orden_inicio, longitud), 100)
        self.assertEqual(calcular_progreso_pct(self.e1.orden_inicio, longitud), 50)
        self.assertEqual(calcular_progreso_pct(self.pelicula.orden_inicio, longitud), 100)

    def test_obra_solo_con_previo_cuenta_entera(self):
        nueva = Obra.objects.create(titulo='Por estrenar longitud', slug='por-estrenar-longitud')
        previo = crear_unidad(nueva, UnidadNarrativa.TIPO_PREVIO, 'Previo al estreno', 1)
        nueva.recalcular_orden()
        previo.refresh_from_db()
        self.assertEqual(longitudes_principales([nueva.id]), {nueva.id: previo.orden_fin})

    def test_landing_al_dia_muestra_100(self):
        usuario = User.objects.create_user('longitud_user', password='x')
        actualizar_progreso(usuario, self.obra, self.e2)
        cliente = APIClient()
        cliente.force_authenticate(user=usuario)
        respuesta = cliente.get(f'/narrative/api/obras/{self.obra.slug}/landing/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['progreso_pct'], 100)