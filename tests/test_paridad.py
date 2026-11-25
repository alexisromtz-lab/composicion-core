import unittest

from composicion_core.corpus import Caso
from composicion_core.paridad import Sonda, puntuar

ROJO = frozenset({"ROJO:t.py::S.test_01_a~t.py::S.test_01_b"})


def _caso(**extra):
    base = dict(
        id="caso",
        descripcion="",
        a={"t.py": "class S:\n  def test_01_a(self):\n    pass\n"},
        b={"t.py": "class S:\n  def test_01_b(self):\n    pass\n"},
        espera_rojos=ROJO,
        espera_avisos=frozenset(),
        espera_no_medido=frozenset(),
        espera_identicos=frozenset(),
        canales=frozenset({"rojo", "aviso", "no_medido"}),
    )
    base.update(extra)
    return Caso(**base)


def _sonda(**extra):
    datos = dict(
        nombre="falsa",
        evaluar=lambda caso: (ROJO, frozenset(), frozenset(), frozenset()),
    )
    datos.update(extra)
    return Sonda(**datos)


class TestPuntuacion(unittest.TestCase):
    def test_una_sonda_conforme_no_tiene_discrepancias(self):
        q = puntuar(_sonda(), [_caso()])
        self.assertEqual(q.rc, 0)
        self.assertEqual(q.acuerdos["rojo"], 1)

    def test_una_sonda_que_no_ve_nada_discrepa(self):
        q = puntuar(_sonda(evaluar=lambda caso: (frozenset(), frozenset(), frozenset(), frozenset())), [_caso()])
        self.assertEqual(q.rc, 1)
        self.assertEqual(q.discrepancias[0].tipo, "rojo")

    def test_una_sonda_que_explota_es_discrepancia_no_verde(self):
        def revienta(caso):
            raise ValueError("byte nulo")

        q = puntuar(_sonda(evaluar=revienta), [_caso()])
        self.assertEqual(q.rc, 1)
        self.assertEqual(q.discrepancias[0].tipo, "fallo")
        self.assertIn("byte nulo", q.discrepancias[0].detalle)

    def test_un_canal_no_afirmado_no_se_puntua(self):
        caso = _caso(canales=frozenset({"no_medido"}), espera_rojos=frozenset(), espera_no_medido=frozenset())
        q = puntuar(_sonda(), [caso])
        self.assertEqual(q.rc, 0)
        self.assertEqual(q.acuerdos.get("rojo"), 0)
        self.assertEqual(q.acuerdos.get("no_medido"), 1)

    def test_una_capacidad_ausente_se_declara_no_comparable(self):
        caso = _caso(espera_no_medido=frozenset({"t.py"}))
        q = puntuar(_sonda(emite_no_medido=False), [caso])
        self.assertEqual(q.rc, 0)
        self.assertEqual(len(q.no_comparables), 1)
        self.assertTrue(q.no_comparables[0][1])

    def test_una_rama_sola_no_se_compara_con_quien_solo_hace_parejas(self):
        caso = _caso(lados=1)
        q = puntuar(_sonda(audita_rama_sola=False), [caso])
        self.assertEqual(len(q.no_comparables), 1)

    def test_una_base_no_soportada_no_se_da_por_buena(self):
        caso = _caso(base={"t.py": ""})
        q = puntuar(_sonda(soporta_base=False), [caso])
        self.assertEqual(len(q.no_comparables), 1)


if __name__ == "__main__":
    unittest.main()
