from django.test import TestCase

from narrative.models import Obra, UnidadNarrativa


class UnidadStrTests(TestCase):
    def test_incluye_el_contenedor_para_distinguir_nombres_repetidos(self):
        obra = Obra.objects.create(titulo='Serie', slug='serie')
        crear = UnidadNarrativa.objects.create
        t1 = crear(obra=obra, tipo='temporada', nombre='Temporada 1', orden_local=1)
        t2 = crear(obra=obra, tipo='temporada', nombre='Segunda · Temporada 1', orden_local=2)
        e1 = crear(obra=obra, tipo='episodio', nombre='Episodio 1', orden_local=1, padre=t1)
        e2 = crear(obra=obra, tipo='episodio', nombre='Episodio 1', orden_local=1, padre=t2)

        self.assertEqual(str(t1), 'Serie · Temporada 1')
        self.assertEqual(str(e1), 'Serie · Temporada 1 · Episodio 1')
        self.assertEqual(str(e2), 'Serie · Segunda · Temporada 1 · Episodio 1')