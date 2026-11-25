import pathlib
import unittest

from composicion_core.adaptadores import cargar, sonda_core
from composicion_core.corpus import carga
from composicion_core.paridad import puntuar

def _hermano(nombre: str) -> pathlib.Path:
    """Los paquetes hermanos se buscan junto a este checkout, no en una ruta fija."""
    return pathlib.Path(__file__).resolve().parents[2] / nombre


HERMANOS = {
    "shadow-guard": _hermano("py-test-shadow-guard"),
    "governor": _hermano("merge-lattice-governor"),
}


class TestNucleoContraSuCorpus(unittest.TestCase):
    def test_el_nucleo_es_conforme_consigo_mismo(self):
        q = puntuar(sonda_core(), carga())
        self.assertEqual(q.discrepancias, [])
        self.assertEqual(q.rc, 0)

    def test_el_corpus_no_deja_casos_sin_comparar_por_capacidad(self):
        q = puntuar(sonda_core(), carga())
        self.assertEqual(q.no_comparables, [])


class TestHermanos(unittest.TestCase):
    """Diferenciales contra los paquetes publicados; se saltan si no están."""

    def _puntua(self, nombre):
        ruta = HERMANOS[nombre]
        if not ruta.exists():
            self.skipTest(f"falta el checkout {ruta}")
        return puntuar(cargar(nombre, str(ruta)), carga())

    def test_el_guardia_respeta_el_corpus(self):
        q = self._puntua("shadow-guard")
        self.assertEqual([d.detalle for d in q.discrepancias], [])
        self.assertEqual(q.rc, 0)

    def test_el_gobernador_respeta_el_corpus(self):
        q = self._puntua("governor")
        self.assertEqual([d.detalle for d in q.discrepancias], [])
        self.assertEqual(q.rc, 0)

    def test_cada_no_comparable_del_gobernador_tiene_su_motivo(self):
        q = self._puntua("governor")
        self.assertTrue(q.no_comparables)
        for caso, motivo in q.no_comparables:
            with self.subTest(caso=caso):
                self.assertTrue(motivo.strip())

    def test_el_gobernador_solo_deja_abierto_el_canal_de_avisos(self):
        """Los otros tres huecos de 0.1.1 se cerraron; si vuelven, el juez lo dice."""
        q = self._puntua("governor")
        self.assertEqual(
            {caso for caso, _ in q.no_comparables},
            {"aviso-global"},
            "rama sola, NO_MEDIDO y duplicado interno deben seguir siendo comparables",
        )


if __name__ == "__main__":
    unittest.main()
