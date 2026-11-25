"""Adaptadores: la misma pregunta, hecha a cada implementación.

Cada adaptador traduce el caso del corpus a la forma que la herramienta
entiende. Los tres devuelven ``(rojos, avisos, no_medidos)`` como conjuntos de
etiquetas, de modo que el orden en que cada una recorra sus pares no cuenta.
"""

from __future__ import annotations

import importlib
import sys

from .corpus import Caso, etiqueta
from .ordinal import AVISO, ROJO, Fuente, colisiones, comparar, leer
from .paridad import Sonda


def _fuentes(crudas: dict[str, str]) -> dict[str, Fuente]:
    return {ruta: leer(texto, ruta) for ruta, texto in crudas.items()}


def evaluar_core(caso: Caso) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    a, b = _fuentes(caso.a), _fuentes(caso.b)
    r = comparar(_fuentes(caso.base or {}), {"a": a, "b": b})
    return (
        frozenset(etiqueta(c.clase, c.a.rotulo(), c.b.rotulo()) for c in r.rojos),
        frozenset(etiqueta(c.clase, c.a.rotulo(), c.b.rotulo()) for c in r.avisos),
        frozenset(clave.split("/", 1)[-1] for clave in r.no_medidos),
    )


def sonda_core() -> Sonda:
    return Sonda("composicion-core", evaluar_core)


def sonda_shadow_guard(nucleo) -> Sonda:
    """``py-test-shadow-guard``: base por pareja, canal de avisos y NO_MEDIDO.

    ``nucleo.leer`` es de la versión que distingue "no tiene tests" de "no pude
    leerlo"; con una versión anterior el canal NO_MEDIDO se declara ausente en
    vez de fingir que la herramienta lo emite.
    """
    tiene_lectura = hasattr(nucleo, "leer")

    def _lee(texto: str, ruta: str):
        return nucleo.leer(texto, ruta) if tiene_lectura else (nucleo.metodos(texto, ruta), None)

    def evaluar(caso: Caso) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
        no_medidos: set[str] = set()

        def _archivos(crudas: dict[str, str], prefijo: str = "") -> dict[str, list]:
            salida = {}
            for ruta, texto in crudas.items():
                salida[ruta], motivo = _lee(texto, ruta)
                if motivo:
                    no_medidos.add(f"{prefijo}{ruta}" if prefijo else ruta)
            return salida

        base = _archivos(caso.base or {}, "base/")
        ramas = {"a": _archivos(caso.a, "a/"), "b": _archivos(caso.b, "b/")}
        r = nucleo.comparar(base, ramas)
        return (
            frozenset(etiqueta(h.clase, h.a.rotulo(), h.b.rotulo()) for h in r.rojos),
            frozenset(etiqueta(h.clase, h.a.rotulo(), h.b.rotulo()) for h in r.avisos),
            frozenset(clave.split("/", 1)[-1] for clave in no_medidos),
        )

    return Sonda(
        "py-test-shadow-guard",
        evaluar,
        soporta_base=True,
        emite_avisos=True,
        emite_no_medido=tiene_lectura,
    )


def sonda_governor(sombra) -> Sonda:
    """``merge-lattice-governor``: sólo parejas del mismo archivo, sin avisos.

    Replica ``parejas._simbolicas`` —intersección de archivos que las dos ramas
    tocan, filtro por la base de la pareja y ``colisiones``— porque la sonda no
    tiene un repositorio git donde llamar a esa función. No audita una rama
    sola: su contrato es una pareja, y ese caso se declara no comparable.
    """
    tiene_nuevos = hasattr(sombra, "nuevos")
    con_nombre = "incluir_mismo_nombre" in getattr(sombra.colisiones, "__kwdefaults__", {}) or False

    def evaluar(caso: Caso) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
        rojos: set[str] = set()
        kwargs = {"incluir_mismo_nombre": True} if con_nombre else {}
        for ruta in sorted(set(caso.a) & set(caso.b)):
            metodos_a = sombra.metodos(caso.a[ruta])
            metodos_b = sombra.metodos(caso.b[ruta])
            if tiene_nuevos:
                heredados = sombra.metodos((caso.base or {}).get(ruta, ""))
                metodos_a = sombra.nuevos(heredados, metodos_a)
                metodos_b = sombra.nuevos(heredados, metodos_b)
            for x, y in sombra.colisiones(metodos_a, metodos_b, **kwargs):
                rojos.add(etiqueta(ROJO, f"{ruta}::{x.rotulo()}", f"{ruta}::{y.rotulo()}"))
        return frozenset(rojos), frozenset(), frozenset()

    return Sonda(
        "merge-lattice-governor",
        evaluar,
        soporta_base=tiene_nuevos,
        emite_avisos=False,
        emite_no_medido=False,
        audita_rama_sola=False,
    )


def cargar(nombre: str, ruta: str) -> Sonda:
    """Importa la herramienta hermana desde un checkout y la envuelve."""
    if ruta not in sys.path:
        sys.path.insert(0, ruta)
    if nombre in ("core", "composicion-core"):
        return sonda_core()
    if nombre in ("shadow-guard", "py-test-shadow-guard"):
        return sonda_shadow_guard(importlib.import_module("py_test_shadow_guard.nucleo"))
    if nombre in ("governor", "merge-lattice-governor"):
        return sonda_governor(importlib.import_module("merge_lattice_governor.sombra"))
    raise SystemExit(f"sonda desconocida: {nombre}")
