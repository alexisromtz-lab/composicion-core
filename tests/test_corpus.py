import unittest

from composicion_core.corpus import carga, etiqueta
from composicion_core.paridad import CANALES


class TestCorpus(unittest.TestCase):
    def test_el_corpus_carga_y_no_repite_identidad(self):
        casos = carga()
        ids = [c.id for c in casos]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(casos), 10)

    def test_cada_caso_declara_universo_y_canales_validos(self):
        for caso in carga():
            with self.subTest(caso=caso.id):
                self.assertTrue(caso.rutas)
                self.assertTrue(caso.canales)
                self.assertTrue(set(caso.canales) <= set(CANALES))
                self.assertIn(caso.lados, (1, 2))

    def test_el_caso_sin_medido_no_afirma_veredicto(self):
        caso = {c.id: c for c in carga()}["byte-nulo"]
        self.assertEqual(set(caso.canales), {"no_medido"})
        self.assertEqual(caso.espera_rojos, frozenset())
        self.assertEqual(caso.espera_avisos, frozenset())

    def test_la_etiqueta_no_depende_del_orden(self):
        self.assertEqual(etiqueta("rojo", "a", "b"), etiqueta("rojo", "b", "a"))


if __name__ == "__main__":
    unittest.main()
