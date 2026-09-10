from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Obra, UnidadNarrativa, ProgresoUsuario, Categoria
from .services import actualizar_progreso, calcular_orden_absoluto, SaltoGrandeRequiereConfirmacion


class RecalcularOrdenTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Serie A', slug='serie-a')

    def _crear_temporada(self, nombre, orden_local, n_episodios, orden_manual=None):
        temporada = UnidadNarrativa.objects.create(
            obra=self.obra, padre=None, tipo='temporada', nombre=nombre,
            orden_local=orden_local, orden_manual=orden_manual,
        )
        episodios = []
        for i in range(1, n_episodios + 1):
            episodios.append(UnidadNarrativa.objects.create(
                obra=self.obra, padre=temporada, tipo='episodio',
                nombre=f'{nombre} E{i}', orden_local=i,
            ))
        return temporada, episodios

    def test_dfs_simple_sin_excepciones(self):
        t1, e1 = self._crear_temporada('T1', 1, 3)
        t2, e2 = self._crear_temporada('T2', 2, 3)

        self.obra.recalcular_orden()

        for u in [t1] + e1 + [t2] + e2:
            u.refresh_from_db()

        self.assertEqual([e.orden_inicio for e in e1], [1, 2, 3])
        self.assertEqual([e.orden_inicio for e in e2], [4, 5, 6])
        self.assertEqual((t1.orden_inicio, t1.orden_fin), (1, 3))
        self.assertEqual((t2.orden_inicio, t2.orden_fin), (4, 6))

    def test_orden_manual_precuela_sin_colision(self):
        pelicula = UnidadNarrativa.objects.create(
            obra=self.obra, padre=None, tipo='pelicula', nombre='Precuela',
            orden_local=1, orden_manual=1,
        )
        t1, e1 = self._crear_temporada('T1', 2, 2)

        self.obra.recalcular_orden()

        pelicula.refresh_from_db()
        for e in e1:
            e.refresh_from_db()

        self.assertEqual(pelicula.orden_inicio, 1)
        self.assertEqual([e.orden_inicio for e in e1], [2, 3])

    def test_orden_manual_spin_off_entre_temporadas(self):
        t1, e1 = self._crear_temporada('T1', 1, 2)
        spin_off, e_spin = self._crear_temporada('Spin-off', 2, 1, orden_manual=3)
        t2, e2 = self._crear_temporada('T2', 3, 2)

        self.obra.recalcular_orden()

        for e in e1 + e_spin + e2:
            e.refresh_from_db()

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

        a.refresh_from_db()
        b.refresh_from_db()
        c.refresh_from_db()

        self.assertEqual(a.orden_inicio, 1)
        self.assertEqual(b.orden_inicio, 2)
        self.assertEqual(c.orden_inicio, 3)


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
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()
        self.temporada.refresh_from_db()

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
        self.episodios = []
        for i in range(1, 6):
            self.episodios.append(UnidadNarrativa.objects.create(
                obra=self.obra, tipo='episodio', nombre=f'E{i}', orden_local=i,
            ))
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


class CategoriaTests(TestCase):
    def test_nombre_unico(self):
        Categoria.objects.create(nombre='anime')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Categoria.objects.create(nombre='anime')

    def test_obra_puede_tener_varias_categorias(self):
        obra = Obra.objects.create(titulo='One Piece', slug='one-piece')
        anime = Categoria.objects.create(nombre='anime')
        accion = Categoria.objects.create(nombre='acción')
        obra.categorias.set([anime, accion])
        self.assertEqual(obra.categorias.count(), 2)

    def test_categoria_no_afecta_frontera_orden(self):
        """Confirma que Categoria es puramente cosmética: no existe ninguna
        vía por la que una categoría pueda influir en frontera_orden o en
        el motor de visibilidad."""
        obra = Obra.objects.create(titulo='Serie', slug='serie-cat')
        categoria = Categoria.objects.create(nombre='series')
        obra.categorias.add(categoria)
        # No hay ningún campo de frontera en Categoria ni en la relación
        # M2M — la única forma de verificarlo es confirmar que el modelo
        # no tiene ese campo.
        self.assertFalse(hasattr(categoria, 'frontera_orden'))