"""Corpus de conformidad: casos con su veredicto esperado, como dato.

El corpus es la especificación. Cada herramienta se puntúa contra él; ninguna
herramienta *es* el corpus, que es lo que evita que dos copias del predicado se
declaren correctas mutuamente.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .ordinal import AVISO, IDENTICO, ROJO

CORPUS = Path(__file__).with_name("corpus") / "casos.json"


@dataclass(frozen=True)
class Caso:
    id: str
    descripcion: str
    a: dict[str, str]
    b: dict[str, str]
    base: dict[str, str] | None = None
    espera_rojos: frozenset[str] = frozenset()
    espera_avisos: frozenset[str] = frozenset()
    espera_no_medido: frozenset[str] = frozenset()
    espera_identicos: frozenset[str] = frozenset()
    canales: frozenset[str] = frozenset(("rojo", "aviso", "no_medido", "identico"))
    lados: int = 2

    @property
    def requiere_base(self) -> bool:
        return self.base is not None

    @property
    def rutas(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.a) | set(self.b) | set(self.base or ())))


def etiqueta(clase: str, rotulo_a: str, rotulo_b: str) -> str:
    """Identidad de un par, independiente del orden en que cada sonda lo emita."""
    prefijo = {ROJO: "ROJO", AVISO: "AVISO", IDENTICO: "IDENTICO"}[clase]
    return f"{prefijo}:{'~'.join(sorted((rotulo_a, rotulo_b)))}"


def _pares(crudos: list[list[str]], clase: str) -> frozenset[str]:
    return frozenset(etiqueta(clase, par[0], par[1]) for par in crudos)


def carga(ruta: Path | None = None) -> list[Caso]:
    datos = json.loads((ruta or CORPUS).read_text(encoding="utf-8"))
    return [
        Caso(
            id=d["id"],
            descripcion=d["descripcion"],
            a=dict(d["a"]),
            b=dict(d["b"]),
            base=dict(d["base"]) if d.get("base") is not None else None,
            espera_rojos=_pares(d.get("espera_rojos", []), ROJO),
            espera_avisos=_pares(d.get("espera_avisos", []), AVISO),
            espera_no_medido=frozenset(d.get("espera_no_medido", [])),
            espera_identicos=_pares(d.get("espera_identicos", []), IDENTICO),
            canales=frozenset(d.get("canales", ("rojo", "aviso", "no_medido", "identico"))),
            lados=int(d.get("lados", 2)),
        )
        for d in datos["casos"]
    ]

