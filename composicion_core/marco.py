"""Medición con marco declarado.

Tercera vez en un día que una cifra correcta mintió por no llevar su marco
(25-Nov-2026): (1) una base global para N ramas dio 76 rojos donde había 1;
(2) la masa de una rama medida contra el tip dio -721 donde contra su propia
base daba 277; (3) ``deuda`` leída como ``holgura`` dio -342,55 sobre un objeto
que estaba en +46,62.

Este módulo no detecta esos errores: hace que sea imposible **construir** el
objeto que los comete. Una ``deuda`` o un ``delta`` sin base y sin techo no se
instancia. Un ``NO_MEDIDO`` (``valor=None``) tiene que declarar ``rc != 0``.
"""

from __future__ import annotations

from dataclasses import dataclass

CLASES = ("conteo", "deuda", "delta")
EXIGEN_MARCO = ("deuda", "delta")


class MarcoIncompleto(ValueError):
    """La medición no declara el marco sin el que su cifra no significa nada."""


@dataclass(frozen=True)
class ResultadoMedido:
    valor: float | int | None
    clase: str
    universo: str
    base: str | None = None
    techo: str | None = None
    rc: int = 0

    def __post_init__(self) -> None:
        if self.clase not in CLASES:
            raise MarcoIncompleto(f"clase desconocida: {self.clase!r}; válidas: {', '.join(CLASES)}")
        if not str(self.universo).strip():
            raise MarcoIncompleto("universo vacío: un conteo sin población no tiene denominador")
        if self.clase in EXIGEN_MARCO:
            for campo in ("base", "techo"):
                if getattr(self, campo) is None or not str(getattr(self, campo)).strip():
                    raise MarcoIncompleto(f"{self.clase} sin {campo}: la cifra no es interpretable")
        if self.valor is None and self.rc == 0:
            raise MarcoIncompleto("NO_MEDIDO (valor=None) exige rc != 0: nunca se degrada a 0")

    def linea(self) -> str:
        if self.valor is None:
            return f"NO_MEDIDO · {self.universo} · rc {self.rc}"
        marco = ""
        if self.clase in EXIGEN_MARCO:
            marco = f" · base {self.base} · techo {self.techo}"
        return f"{self.valor} ({self.clase}) · {self.universo}{marco} · rc {self.rc}"
