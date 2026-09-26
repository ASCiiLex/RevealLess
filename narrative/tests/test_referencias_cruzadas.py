from django.test import TestCase

from ..models import Obra
from ..services import detectar_posibles_referencias_cruzadas


class DeteccionReferenciaCruzadaTests(TestCase):
    def setUp(self):
        self.anime = Obra.objects.create(titulo='One Piece Anime', slug='op-anime', tipo=Obra.TIPO_SERIE)
        self.manga = Obra.objects.create(
            titulo='One Piece Manga', slug='op-manga', tipo=Obra.TIPO_MANGA, adapta_a=self.anime,
        )

    def test_detecta_palabra_manga_cuando_hay_manga_relacionado(self):
        detecciones = detectar_posibles_referencias_cruzadas('esto pasó en el manga', self.anime)
        self.assertEqual(len(detecciones), 1)
        self.assertEqual(detecciones[0]['obra'], self.manga)
        self.assertEqual(detecciones[0]['palabra'], 'manga')

    def test_detecta_en_sentido_inverso_de_adapta_a(self):
        """Desde el manga, 'anime' detecta la obra origen (dirección hijo -> padre)."""
        detecciones = detectar_posibles_referencias_cruzadas('en el anime esto no pasó así', self.manga)
        self.assertEqual(len(detecciones), 1)
        self.assertEqual(detecciones[0]['obra'], self.anime)

    def test_no_detecta_sin_relacion_adapta_a(self):
        suelta = Obra.objects.create(titulo='Otra serie', slug='otra-serie')
        self.assertEqual(detectar_posibles_referencias_cruzadas('esto pasó en el manga', suelta), [])

    def test_case_insensitive(self):
        detecciones = detectar_posibles_referencias_cruzadas('MANGA en mayúsculas', self.anime)
        self.assertEqual(len(detecciones), 1)

    def test_no_hay_falso_positivo_por_substring_sin_limite_de_palabra(self):
        """'mangaka' contiene 'manga' pero no como palabra completa (\\b)."""
        self.assertEqual(detectar_posibles_referencias_cruzadas('es un mangaka reconocido', self.anime), [])

    def test_texto_sin_palabra_clave_no_detecta(self):
        self.assertEqual(
            detectar_posibles_referencias_cruzadas('un texto normal sin nada especial', self.anime), [],
        )