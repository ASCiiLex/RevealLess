from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from narrative.models import (
    EtapaPersonaje, Obra, Personaje, PropuestaAparicion, RelevanciaPersonaje, UnidadNarrativa,
)
from narrative.services.personajes import aprobar_propuesta


def _obra(slug, grupos, tipo_grupo, con_episodios):
    obra = Obra.objects.create(titulo=slug, slug=slug)
    unidades = {}
    for i, nombre in enumerate(grupos, 1):
        grupo = UnidadNarrativa.objects.create(obra=obra, tipo=tipo_grupo, nombre=nombre, orden_local=i)
        unidades[nombre] = grupo
        if con_episodios:
            unidades[f'{nombre}/ep'] = UnidadNarrativa.objects.create(
                obra=obra, tipo='episodio', nombre=f'E{i}', orden_local=1, padre=grupo,
            )
    obra.recalcular_orden()
    return obra, unidades


def _aparicion(personaje, unidad):
    aprobar_propuesta(PropuestaAparicion.objects.create(personaje=personaje, unidad=unidad))


class CopiarPersonajesTests(TestCase):
    def setUp(self):
        self.anime, self.ua = _obra('anime', ['Arco de la isla Whole Cake', 'Arco del País de Wano (parte 2)'], 'arco', True)
        self.manga, self.um = _obra('manga', ['Arco de Whole Cake Island', 'Arco del País de Wano'], 'arco', False)
        self.luffy = Personaje.objects.create(nombre='Luffy')
        _aparicion(self.luffy, self.ua['Arco del País de Wano (parte 2)/ep'])
        RelevanciaPersonaje.objects.create(personaje=self.luffy, obra=self.anime, nivel=RelevanciaPersonaje.NIVEL_PROTAGONISTA)
        EtapaPersonaje.objects.create(
            personaje=self.luffy, visible_tras=self.ua['Arco de la isla Whole Cake'],
            nota='Recompensa: 1.500.000.000 ฿', imagen='cartel.jpg',
        )

    def _copiar(self, *args):
        call_command('copiar_personajes', '--desde', 'anime', '--hasta', 'manga', *args, stdout=StringIO())

    def test_un_episodio_se_copia_a_su_arco_equivalente(self):
        self._copiar()
        self.assertEqual(list(self.luffy.unidades.filter(obra=self.manga)), [self.um['Arco del País de Wano']])

    def test_copia_relevancia_y_etapas_con_imagen(self):
        self._copiar('--etapas')
        self.assertEqual(
            RelevanciaPersonaje.objects.get(personaje=self.luffy, obra=self.manga).nivel,
            RelevanciaPersonaje.NIVEL_PROTAGONISTA,
        )
        etapa = EtapaPersonaje.objects.get(personaje=self.luffy, visible_tras=self.um['Arco de Whole Cake Island'])
        self.assertEqual((etapa.nota, etapa.imagen.name), ('Recompensa: 1.500.000.000 ฿', 'cartel.jpg'))

    def test_completa_la_imagen_de_una_etapa_que_ya_existia(self):
        EtapaPersonaje.objects.create(
            personaje=self.luffy, visible_tras=self.um['Arco de Whole Cake Island'], nota='Recompensa: 1.500.000.000 ฿',
        )
        self._copiar('--etapas')
        etapa = EtapaPersonaje.objects.get(personaje=self.luffy, visible_tras=self.um['Arco de Whole Cake Island'])
        self.assertEqual(etapa.imagen.name, 'cartel.jpg')

    def test_dry_run_no_guarda_nada(self):
        self._copiar('--etapas', '--dry-run')
        self.assertFalse(self.luffy.unidades.filter(obra=self.manga).exists())
        self.assertFalse(RelevanciaPersonaje.objects.filter(obra=self.manga).exists())
        self.assertFalse(EtapaPersonaje.objects.filter(visible_tras__obra=self.manga).exists())

    def test_titulo_con_subtitulo_empareja_con_el_principal(self):
        pelis, up = _obra('pelis', ['El Hobbit: Un viaje inesperado'], 'pelicula', False)
        libros, ul = _obra('libros', ['El Hobbit'], 'libro', False)
        bilbo = Personaje.objects.create(nombre='Bilbo')
        _aparicion(bilbo, up['El Hobbit: Un viaje inesperado'])
        call_command('copiar_personajes', '--desde', 'pelis', '--hasta', 'libros', stdout=StringIO())
        self.assertEqual(list(bilbo.unidades.filter(obra=libros)), [ul['El Hobbit']])