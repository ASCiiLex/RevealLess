from django.contrib.auth.models import User
from django.test import TestCase

from ..models import Obra, UnidadNarrativa
from ..services import (
    actualizar_progreso,
    calcular_orden_absoluto,
    SaltoGrandeRequiereConfirmacion,
)


class ProgresoUsuarioTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('lector', password='x')
        self.obra = Obra.objects.create(titulo='Serie B', slug='serie-b')
        self.temporada = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='temporada', nombre='T1', orden_local=1,
        )
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, padre=self.temporada, tipo='episodio',
            nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, padre=self.temporada, tipo='episodio',
            nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        for u in (self.e1, self.e2, self.temporada):
            u.refresh_from_db()

    def test_progreso_a_nivel_de_hoja_usa_orden_inicio(self):
        self.assertEqual(calcular_orden_absoluto(self.e2), self.e2.orden_inicio)

    def test_progreso_a_nivel_de_bloque_es_conservador(self):
        self.assertEqual(
            calcular_orden_absoluto(self.temporada),
            self.temporada.orden_inicio - 1,
        )

    def test_no_se_permite_retroceder(self):
        actualizar_progreso(self.user, self.obra, self.e2)
        with self.assertRaises(ValueError):
            actualizar_progreso(self.user, self.obra, self.e1)

    def test_se_permite_avanzar(self):
        actualizar_progreso(self.user, self.obra, self.e1)
        progreso = actualizar_progreso(self.user, self.obra, self.e2)
        self.assertEqual(progreso.unidad_actual, self.e2)
        self.assertEqual(progreso.orden_absoluto, self.e2.orden_inicio)


class SaltoGrandeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('lector2', password='x')
        self.obra = Obra.objects.create(titulo='Serie C', slug='serie-c')
        self.episodios = [
            UnidadNarrativa.objects.create(
                obra=self.obra, tipo='episodio', nombre=f'E{i}', orden_local=i,
            )
            for i in range(1, 6)
        ]
        self.obra.recalcular_orden()
        for e in self.episodios:
            e.refresh_from_db()

    def test_salto_pequeno_no_requiere_confirmacion(self):
        actualizar_progreso(self.user, self.obra, self.episodios[0])
        progreso = actualizar_progreso(self.user, self.obra, self.episodios[1])
        self.assertEqual(progreso.unidad_actual, self.episodios[1])

    def test_salto_grande_requiere_confirmacion(self):
        actualizar_progreso(self.user, self.obra, self.episodios[0])
        with self.assertRaises(SaltoGrandeRequiereConfirmacion):
            actualizar_progreso(self.user, self.obra, self.episodios[4])

    def test_salto_grande_confirmado_se_aplica(self):
        actualizar_progreso(self.user, self.obra, self.episodios[0])
        progreso = actualizar_progreso(self.user, self.obra, self.episodios[4], confirmado=True)
        self.assertEqual(progreso.unidad_actual, self.episodios[4])