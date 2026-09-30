import datetime
from types import SimpleNamespace

from django.test import SimpleTestCase

from narrative.management.commands.importar_personajes import emparejar


def unidad(id_, nombre, fecha):
    return SimpleNamespace(id=id_, nombre=nombre, fecha=fecha)


def parte(qid, titulo, *fechas, personajes=1):
    return {
        'qid': qid, 'titulo': titulo, 'fechas': list(fechas),
        'personajes': [{'qid': f'P{i}', 'nombre': str(i)} for i in range(personajes)],
    }


class EmparejarTests(SimpleTestCase):
    def test_empareja_por_fecha_cercana_aunque_no_sea_exacta(self):
        u = unidad(1, 'Los Vengadores', datetime.date(2012, 4, 27))
        resultado = emparejar([parte('Q1', 'The Avengers', datetime.date(2012, 4, 25))], [u])
        self.assertEqual(resultado, {'Q1': u})

    def test_usa_la_fecha_mas_cercana_de_todas_las_de_la_parte(self):
        u = unidad(1, 'Los Vengadores', datetime.date(2012, 4, 27))
        premiere_lejana = datetime.date(2011, 7, 15)
        resultado = emparejar([parte('Q1', 'The Avengers', premiere_lejana, datetime.date(2012, 4, 25))], [u])
        self.assertEqual(resultado, {'Q1': u})

    def test_una_parte_ajena_no_roba_la_unidad_ya_emparejada_por_titulo(self):
        thor = unidad(1, 'Thor: Ragnarok', datetime.date(2017, 11, 3))
        partes = [
            parte('Q10', 'Thor: Ragnarok'),
            parte('Q20', 'Havoc in the Hidden Land', datetime.date(2017, 11, 3)),
        ]
        self.assertEqual(emparejar(partes, [thor]), {'Q10': thor})

    def test_por_fecha_solo_cuentan_partes_con_personajes(self):
        pelicula = unidad(1, 'Shang-Chi', datetime.date(2021, 9, 3))
        partes = [
            parte('Q1', 'Episodio', datetime.date(2021, 9, 1), personajes=0),
            parte('Q9', 'Shang-Chi and the Legend of the Ten Rings', datetime.date(2021, 9, 1)),
        ]
        self.assertEqual(emparejar(partes, [pelicula]), {'Q9': pelicula})

    def test_episodios_estrenados_el_mismo_dia_no_se_emparejan(self):
        dia = datetime.date(2015, 4, 10)
        unidades = [unidad(1, 'Condenado', dia), unidad(2, 'Stick', dia)]
        partes = [parte('Q1', 'Cut Man', dia), parte('Q2', 'Condemned', dia)]
        self.assertEqual(emparejar(partes, unidades), {})

    def test_fuera_de_la_ventana_no_empareja(self):
        u = unidad(1, 'Algo', datetime.date(2020, 1, 1))
        self.assertEqual(emparejar([parte('Q1', 'Otra', datetime.date(2020, 3, 1))], [u]), {})