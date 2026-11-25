"""Puntuación de una herramienta contra el corpus.

No compara dos herramientas entre sí: compara cada una contra la
especificación. Dos implementaciones de acuerdo no son evidencia de nada; una
implementación de acuerdo con el corpus sí, y su desacuerdo dice qué caso y en
qué canal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .corpus import Caso

CANALES = ("rojo", "aviso", "no_medido", "identico")

Evalua = Callable[[Caso], tuple[frozenset[str], frozenset[str], frozenset[str], frozenset[str]]]


@dataclass(frozen=True)
class Sonda:
    """Una implementación bajo prueba. Declara lo que *puede* emitir.

    Lo declarado no la absuelve: sólo evita puntuar como fallo un canal que la
    herramienta no tiene, y ese caso se publica como ``NO_COMPARABLE``.
    """

    nombre: str
    evaluar: Evalua
    soporta_base: bool = True
    emite_avisos: bool = True
    emite_no_medido: bool = True
    emite_identico: bool = True
    audita_rama_sola: bool = True


@dataclass
class Discrepancia:
    caso: str
    tipo: str
    esperado: list[str] = field(default_factory=list)
    obtenido: list[str] = field(default_factory=list)
    detalle: str = ""


@dataclass
class Puntuacion:
    sonda: Sonda
    acuerdos: dict[str, int] = field(default_factory=lambda: {c: 0 for c in CANALES})
    discrepancias: list[Discrepancia] = field(default_factory=list)
    no_comparables: list[tuple[str, str]] = field(default_factory=list)

    @property
    def rc(self) -> int:
        return 1 if self.discrepancias else 0

    @property
    def casos_totales(self) -> int:
        return sum(self.acuerdos.values()) + len({d.caso for d in self.discrepancias}) + len(self.no_comparables)

    def lineas(self) -> list[str]:
        salida = [
            f"{self.sonda.nombre}: {self.acuerdos['rojo']} rojo · {self.acuerdos['aviso']} aviso · "
            f"{self.acuerdos['no_medido']} no_medido · {self.acuerdos['identico']} identico · "
            f"{len(self.discrepancias)} discrepancias · {len(self.no_comparables)} no comparables"
        ]
        for d in self.discrepancias:
            if d.tipo == "fallo":
                salida.append(f"  FALLO        {d.caso}: {d.detalle}")
            else:
                salida.append(f"  DISCREPANCIA {d.caso} [{d.tipo}] esperado={d.esperado} obtenido={d.obtenido}")
        for caso, motivo in self.no_comparables:
            salida.append(f"  NO_COMPARABLE {caso}: {motivo}")
        return salida

    def como_dict(self) -> dict:
        return {
            "sonda": self.sonda.nombre,
            "acuerdos": dict(self.acuerdos),
            "discrepancias": [vars(d) for d in self.discrepancias],
            "no_comparables": [{"caso": c, "motivo": m} for c, m in self.no_comparables],
            "rc": self.rc,
        }


def _capacidades(sonda: Sonda, caso: Caso) -> str | None:
    """Lo que la herramienta declara no tener se publica, no se puntúa como fallo.

    El filtro sólo actúa sobre canales que el caso **afirma**: un caso que no
    declara ``no_medido`` sí ejerce la herramienta, y ahí un traceback sí es una
    discrepancia. Gatear antes de invocar era esconder el defecto.
    """
    if caso.requiere_base and not sonda.soporta_base:
        return "no soporta base por pareja"
    if caso.lados == 1 and not sonda.audita_rama_sola:
        return "sólo compone parejas, no audita una rama sola"
    if "aviso" in caso.canales and caso.espera_avisos and not sonda.emite_avisos:
        return "no tiene canal de avisos"
    if "no_medido" in caso.canales and caso.espera_no_medido and not sonda.emite_no_medido:
        return "no publica NO_MEDIDO"
    if "identico" in caso.canales and caso.espera_identicos and not sonda.emite_identico:
        return "no distingue el duplicado idéntico"
    return None


def puntuar(sonda: Sonda, casos: list[Caso]) -> Puntuacion:
    puntuacion = Puntuacion(sonda)
    for caso in casos:
        motivo = _capacidades(sonda, caso)
        if motivo is not None:
            puntuacion.no_comparables.append((caso.id, motivo))
            continue
        try:
            rojos, avisos, no_medidos, identicos = sonda.evaluar(caso)
        except Exception as exc:  # una sonda que explota no es un veredicto
            puntuacion.discrepancias.append(
                Discrepancia(caso.id, "fallo", detalle=f"{type(exc).__name__}: {exc}")
            )
            continue
        for canal, esperado, obtenido in (
            ("rojo", caso.espera_rojos, rojos),
            ("aviso", caso.espera_avisos, avisos),
            ("no_medido", caso.espera_no_medido, no_medidos),
            ("identico", caso.espera_identicos, identicos),
        ):
            if canal not in caso.canales:
                continue
            if esperado == obtenido:
                puntuacion.acuerdos[canal] += 1
            else:
                puntuacion.discrepancias.append(
                    Discrepancia(caso.id, canal, sorted(esperado), sorted(obtenido))
                )
    return puntuacion
