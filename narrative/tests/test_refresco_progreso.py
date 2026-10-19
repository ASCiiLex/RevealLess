from django.contrib.auth.models import User
from django.test import TestCase

from narrative.models import ProgresoUsuario, UnidadNarrativa
from narrative.services import actualizar_progreso
from posts.tests.utils import crear_obra


class RefrescoProgresoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('lector_refresco', password='x')
        self.obra, (self.u1, self.u2) = crear_obra('refresco-progreso', n=2)

    def _progreso(self):
        return ProgresoUsuario.objects.get(usuario=self.usuario, obra=self.obra).orden_absoluto

    def test_insertar_antes_desplaza_el_progreso_con_su_unidad(self):
        actualizar_progreso(self.usuario, self.obra, self.u2)
        self.assertEqual(self._progreso(), 2)

        UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Insertado', orden_local=3, orden_manual=1)
        self.obra.recalcular_orden()

        self.assertEqual(self._progreso(), 3)

    def test_borrar_antes_no_deja_el_progreso_por_delante(self):
        actualizar_progreso(self.usuario, self.obra, self.u2)
        self.u1.delete()
        self.obra.recalcular_orden()

        self.assertEqual(self._progreso(), 1)