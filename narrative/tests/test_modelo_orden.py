from django.test import TestCase

from ..models import Obra, UnidadNarrativa


class RecalcularOrdenTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Serie A', slug='serie-a')

    def _crear_temporada(self, nombre, orden_local, n_episodios, orden_manual=None):
        temporada = UnidadNarrativa.objects.create(
            obra=self.obra, padre=None, tipo='temporada', nombre=nombre,
            orden_local=orden_local, orden_manual=orden_manual,
        )
        episodios = [
            UnidadNarrativa.objects.create(
                obra=self.obra, padre=temporada, tipo='episodio',
                nombre=f'{nombre} E{i}', orden_local=i,
            )
            for i in range(1, n_episodios + 1)
        ]
        return temporada, episodios

    @staticmethod
    def _refrescar(*unidades):
        for u in unidades:
            u.refresh_from_db()

    def test_dfs_simple_sin_excepciones(self):
        t1, e1 = self._crear_temporada('T1', 1, 3)
        t2, e2 = self._crear_temporada('T2', 2, 3)

        self.obra.recalcular_orden()
        self._refrescar(t1, *e1, t2, *e2)

        self.assertEqual([e.orden_inicio for e in e1], [1, 2, 3])
        self.assertEqual([e.orden_inicio for e in e2], [4, 5, 6])
        self.assertEqual((t1.orden_inicio, t1.orden_fin), (1, 3))
        self.assertEqual((t2.orden_inicio, t2.orden_fin), (4, 6))

    def test_orden_manual_precuela_sin_colision(self):
        pelicula = UnidadNarrativa.objects.create(
            obra=self.obra, padre=None, tipo='pelicula', nombre='Precuela',
            orden_local=1, orden_manual=1,
        )
        _, e1 = self._crear_temporada('T1', 2, 2)

        self.obra.recalcular_orden()
        self._refrescar(pelicula, *e1)

        self.assertEqual(pelicula.orden_inicio, 1)
        self.assertEqual([e.orden_inicio for e in e1], [2, 3])

    def test_orden_manual_spin_off_entre_temporadas(self):
        _, e1 = self._crear_temporada('T1', 1, 2)
        _, e_spin = self._crear_temporada('Spin-off', 2, 1, orden_manual=3)
        _, e2 = self._crear_temporada('T2', 3, 2)

        self.obra.recalcular_orden()
        self._refrescar(*e1, *e_spin, *e2)

        self.assertEqual([e.orden_inicio for e in e1], [1, 2])
        self.assertEqual(e_spin[0].orden_inicio, 3)
        self.assertEqual([e.orden_inicio for e in e2], [4, 5])

    def test_empate_en_indice_manual_se_desempata_por_dfs(self):
        a = UnidadNarrativa.objects.create(
            obra=self.obra, padre=None, tipo='especial', nombre='A',
            orden_local=1, orden_manual=1,
        )
        b = UnidadNarrativa.objects.create(
            obra=self.obra, padre=None, tipo='especial', nombre='B',
            orden_local=2, orden_manual=1,
        )
        c = UnidadNarrativa.objects.create(
            obra=self.obra, padre=None, tipo='especial', nombre='C',
            orden_local=3,
        )

        self.obra.recalcular_orden()
        self._refrescar(a, b, c)

        self.assertEqual(a.orden_inicio, 1)
        self.assertEqual(b.orden_inicio, 2)
        self.assertEqual(c.orden_inicio, 3)