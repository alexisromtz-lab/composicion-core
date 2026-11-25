import unittest

from composicion_core.marco import MarcoIncompleto, ResultadoMedido


class TestMarcoDeclarado(unittest.TestCase):
    def test_una_deuda_sin_techo_no_se_construye(self):
        with self.assertRaises(MarcoIncompleto):
            ResultadoMedido(valor=721, clase="deuda", universo="origin/main", base="34ee1d2c")

    def test_un_delta_sin_base_no_se_construye(self):
        with self.assertRaises(MarcoIncompleto):
            ResultadoMedido(valor=-721, clase="delta", universo="origin/main", techo="10486")

    def test_el_mismo_numero_con_su_marco_si(self):
        r = ResultadoMedido(
            valor=-721,
            clase="delta",
            universo="origin/main",
            base="34ee1d2c",
            techo="10486",
        )
        self.assertIn("base 34ee1d2c", r.linea())
        self.assertIn("techo 10486", r.linea())

    def test_un_conteo_no_necesita_marco(self):
        self.assertIn("3", ResultadoMedido(valor=3, clase="conteo", universo="tests/").linea())

    def test_no_medido_no_se_degrada_a_cero(self):
        with self.assertRaises(MarcoIncompleto):
            ResultadoMedido(valor=None, clase="conteo", universo="tests/")
        self.assertIn("NO_MEDIDO", ResultadoMedido(valor=None, clase="conteo", universo="tests/", rc=2).linea())

    def test_un_universo_vacio_no_tiene_denominador(self):
        with self.assertRaises(MarcoIncompleto):
            ResultadoMedido(valor=0, clase="conteo", universo="  ")

    def test_una_clase_inventada_se_rechaza(self):
        with self.assertRaises(MarcoIncompleto):
            ResultadoMedido(valor=1, clase="holgura", universo="origin/main")


if __name__ == "__main__":
    unittest.main()
