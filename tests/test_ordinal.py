import unittest

from composicion_core.ordinal import (
    Fuente,
    colisiones,
    comparar,
    leer,
    metodos,
    nuevos,
    ordinal,
)


class TestExtraccion(unittest.TestCase):
    def test_ordinal_del_nombre(self):
        self.assertEqual(ordinal("test_07_alpha"), 7)
        self.assertEqual(ordinal("test7"), 7)
        self.assertIsNone(ordinal("test_algo"))
        self.assertIsNone(ordinal("no_es_test"))

    def test_clase_anidada_conserva_el_prefijo(self):
        fuente = leer("class A:\n  class B:\n    def test_01_x(self):\n      pass\n", "t.py")
        self.assertEqual([m.clase for m in fuente.metodos], ["A.B"])

    def test_un_archivo_ilegible_no_tiene_cero_metodos(self):
        fuente = leer("def (:", "t.py")
        self.assertEqual(tuple(fuente.metodos), ())
        self.assertFalse(fuente.medida)
        self.assertIn("sintaxis", fuente.error)

    def test_byte_nulo_no_revienta_y_no_se_mide(self):
        fuente = leer("x = 1\x00y = 2\n", "t.py")
        self.assertFalse(fuente.medida)
        self.assertTrue(fuente.error)

    def test_metodos_es_un_atajo_tolerante(self):
        self.assertEqual(tuple(metodos("def (:", "t.py")), ())


class TestColisiones(unittest.TestCase):
    def test_mismo_nombre_en_la_misma_clase_pierde_un_test(self):
        a = leer("class S:\n  def test_algo(self):\n    pass\n", "t.py").metodos
        b = leer("class S:\n  def test_algo(self):\n    return 2\n", "t.py").metodos
        self.assertEqual(len(colisiones(a, b)), 1)
        self.assertEqual(colisiones(a, b)[0].clase, "rojo")

    def test_mismo_ordinal_distinto_nombre_es_rojo_por_convencion(self):
        a = leer("class S:\n  def test_35_a(self):\n    pass\n", "t.py").metodos
        b = leer("class S:\n  def test_35_b(self):\n    pass\n", "t.py").metodos
        self.assertEqual(colisiones(a, b)[0].clase, "rojo")

    def test_mismo_ordinal_en_clases_distintas_es_aviso(self):
        a = leer("class A:\n  def test_35_a(self):\n    pass\n", "t.py").metodos
        b = leer("class B:\n  def test_35_b(self):\n    pass\n", "t.py").metodos
        self.assertEqual(colisiones(a, b)[0].clase, "aviso")

    def test_sin_ordinal_y_con_nombres_distintos_no_es_nada(self):
        a = leer("class S:\n  def test_alfa(self):\n    pass\n", "t.py").metodos
        b = leer("class S:\n  def test_beta(self):\n    pass\n", "t.py").metodos
        self.assertEqual(colisiones(a, b), [])

    def test_compararse_consigo_mismo_no_duplica_ni_se_autocolisiona(self):
        lista = leer(
            "class S:\n  def test_07_a(self):\n    pass\n\n  def test_07_b(self):\n    pass\n", "t.py"
        ).metodos
        pares = colisiones(lista, lista)
        self.assertEqual(len(pares), 1)
        self.assertIsNot(pares[0].a, pares[0].b)


class TestComparar(unittest.TestCase):
    def test_lo_heredado_de_la_base_no_dispara(self):
        comun = "class S:\n  def test_algo(self):\n    pass\n"
        r = comparar(
            {"t.py": leer(comun, "t.py")},
            {
                "a": {"t.py": leer(comun + "\n  def test_40_a(self):\n    pass\n", "t.py")},
                "b": {"t.py": leer(comun + "\n  def test_40_b(self):\n    pass\n", "t.py")},
            },
        )
        self.assertEqual(len(r.rojos), 1)
        self.assertEqual(r.ingenuo, 1)

    def test_duplicado_dentro_de_una_rama_es_rojo(self):
        fuente = "class S:\n  def test_07_a(self):\n    pass\n\n  def test_07_b(self):\n    pass\n"
        r = comparar({}, {"a": {"t.py": leer(fuente, "t.py")}})
        self.assertEqual(len(r.rojos), 1)

    def test_una_fuente_ilegible_entra_como_no_medida(self):
        r = comparar({"t.py": leer("def (:", "t.py")}, {"a": {"t.py": Fuente("t.py")}})
        self.assertEqual(len(r.no_medidos), 1)
        self.assertIn("t.py", r.no_medidos[0])

    def test_nuevos_sin_base_es_todo(self):
        self.assertEqual(len(nuevos(None, leer("class S:\n  def test_01_x(self):\n    pass\n", "t.py"))), 1)


if __name__ == "__main__":
    unittest.main()
