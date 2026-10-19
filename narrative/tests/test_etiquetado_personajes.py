from django.contrib.auth.models import User
from django.test import TestCase

from narrative.models import EtapaPersonaje, Personaje
from narrative.services.etiquetado import etiquetar_personajes, personajes_mencionados
from posts.tests.utils import crear_obra, crear_post


class PersonajesMencionadosTests(TestCase):
    def setUp(self):
        self.obra, self.ep = crear_obra('obra-etiquetado', 3)

    def _personaje(self, nombre, unidad):
        p = Personaje.objects.create(nombre=nombre)
        p.unidades.add(unidad)
        return p

    def _menciona(self, texto, hasta):
        return personajes_mencionados(texto, self.obra.id, hasta.orden_fin)

    def test_nombre_completo_sin_tildes_ni_mayusculas(self):
        ana = self._personaje('Ana Pérez', self.ep[0])
        self.assertEqual(self._menciona('qué grande ana perez', self.ep[0]), {ana.id})

    def test_palabra_suelta_que_identifica_a_uno(self):
        zoro = self._personaje('Roronoa Zoro', self.ep[0])
        self.assertEqual(self._menciona('Zoro se pierde otra vez', self.ep[0]), {zoro.id})

    def test_nombre_de_una_palabra_en_minusculas_sigue_etiquetando(self):
        nami = self._personaje('Nami', self.ep[0])
        self.assertEqual(self._menciona('nami dibuja mapas', self.ep[0]), {nami.id})

    def test_palabra_ambigua_no_etiqueta(self):
        self._personaje('Monkey D. Luffy', self.ep[0])
        self._personaje('Monkey D. Garp', self.ep[0])
        self.assertEqual(self._menciona('Monkey es un apellido curioso', self.ep[0]), set())

    def test_respeta_limites_de_palabra(self):
        self._personaje('Ana', self.ep[0])
        self.assertEqual(self._menciona('me como una banana', self.ep[0]), set())

    def test_palabra_comun_en_minusculas_no_etiqueta(self):
        self._personaje('Han Solo', self.ep[0])
        self.assertEqual(self._menciona('sin contar la Fuerza, sólo habilidad con la espada', self.ep[0]), set())
        self.assertEqual(self._menciona('es solo una opinión', self.ep[0]), set())

    def test_palabra_comun_con_mayuscula_etiqueta(self):
        han = self._personaje('Han Solo', self.ep[0])
        self.assertEqual(self._menciona('y entonces Solo dispara primero', self.ep[0]), {han.id})

    def test_nombre_corriente_de_una_palabra_exige_mayuscula(self):
        rey = self._personaje('Rey', self.ep[0])
        self.assertEqual(self._menciona('el rey del norte', self.ep[0]), set())
        self.assertEqual(self._menciona('la pelea de Rey con Kylo', self.ep[0]), {rey.id})

    def test_no_etiqueta_personajes_posteriores_a_la_frontera(self):
        self._personaje('Shanks', self.ep[2])
        self.assertEqual(self._menciona('Shanks aparece', self.ep[0]), set())

    def test_alias_solo_si_ya_se_ha_revelado(self):
        wanda = self._personaje('Wanda Maximoff', self.ep[0])
        EtapaPersonaje.objects.create(personaje=wanda, visible_tras=self.ep[1], alias='Bruja Escarlata')
        self.assertEqual(self._menciona('la Bruja Escarlata', self.ep[0]), set())
        self.assertEqual(self._menciona('la Bruja Escarlata', self.ep[1]), {wanda.id})

    def test_etiquetar_sustituye_las_anteriores(self):
        autor = User.objects.create_user('etiquetador', password='x')
        nami = self._personaje('Nami', self.ep[0])
        usopp = self._personaje('Usopp', self.ep[0])
        post = crear_post(autor, self.obra, self.ep[0], text='Nami dibuja mapas')
        post.personajes.add(usopp)
        etiquetar_personajes(post)
        self.assertEqual(list(post.personajes.all()), [nami])