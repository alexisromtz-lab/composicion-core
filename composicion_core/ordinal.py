"""Predicado canónico de colisión de tests: el que las dos herramientas acatan.

Medición de origen (25-Nov-2026, repo desechable de tres ramas): dos ramas insertan
``def test_algo`` en puntos distintos de la **misma** clase. ``git merge-tree``
devuelve RC 0 y cero marcas ``<<<<<<< .our``; el merge real entra limpio y deja
el archivo con 42 ``def`` y 41 nombres distintos. Python conserva el último y el
CI queda verde **con un test menos**. No es un conflicto textual: ninguna
herramienta que sólo mire ``merge-tree`` puede verlo.

De ahí las dos reglas del predicado, y por qué son dos:

* **misma clase + mismo nombre** → ROJO. Es el borrado silencioso de arriba.
* **misma clase + mismo ordinal + nombre distinto** → ROJO *por política*, no
  por semántica: los dos métodos sobreviven y los dos corren. Lo que se rompe es
  la numeración, que es el mecanismo con el que se coordinan los autores y los
  agentes para saber qué test es cuál. Se clasifica igual que el borrado porque
  el veredicto ya está tomado en el corpus: el defecto de ``ElPredicadoMuerde.
  test_35`` no perdió un test, perdió la capacidad de nombrarlos.
* **clases distintas + mismo ordinal + nombre distinto** → AVISO. No rompe la
  ejecución; degrada la trazabilidad.

Y una condición de honestidad: un archivo que no compila **no tiene cero
métodos**, tiene métodos desconocidos. Por eso ``leer`` devuelve ``Fuente`` con
``error`` y el llamador debe publicar ``NO_MEDIDO``, no una lista vacía.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

_ORDINAL = re.compile(r"^test_?(\d+)")

ROJO = "rojo"
AVISO = "aviso"


def ordinal(nombre: str) -> int | None:
    """Prefijo numérico de ``test_35_algo`` / ``test35_algo``, o ``None``."""
    encontrado = _ORDINAL.match(nombre)
    return int(encontrado.group(1)) if encontrado else None


@dataclass(frozen=True)
class Metodo:
    ruta: str
    clase: str
    nombre: str
    linea: int

    @property
    def ordinal(self) -> int | None:
        return ordinal(self.nombre)

    @property
    def clave(self) -> tuple[str, str]:
        return (self.ruta, self.clase)

    def rotulo(self) -> str:
        cual = f"{self.clase}.{self.nombre}" if self.clase else self.nombre
        return f"{self.ruta}::{cual}"


@dataclass(frozen=True)
class Fuente:
    """Resultado de leer un archivo: métodos medidos, o el motivo de no medirlos."""

    ruta: str
    metodos: tuple[Metodo, ...] = ()
    error: str | None = None

    @property
    def medida(self) -> bool:
        return self.error is None


@dataclass(frozen=True)
class Colision:
    clase: str
    a: Metodo
    b: Metodo
    motivo: str

    def rotulo(self) -> str:
        etiqueta = "ROJO" if self.clase == ROJO else "AVISO"
        return f"{etiqueta}  {self.a.rotulo()}  vs  {self.b.rotulo()}   ({self.motivo})"


def _recorre(cuerpo: list[ast.stmt], prefijo: str, ruta: str, salida: list[Metodo]) -> None:
    for nodo in cuerpo:
        if isinstance(nodo, ast.ClassDef):
            _recorre(nodo.body, f"{prefijo}{nodo.name}.", ruta, salida)
        elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if nodo.name.startswith("test"):
                salida.append(Metodo(ruta, prefijo.rstrip("."), nodo.name, nodo.lineno))


def leer(fuente: str, ruta: str) -> Fuente:
    """AST de un archivo de tests. ``SyntaxError`` y ``ValueError`` no explotan.

    Un byte nulo llega como ``ValueError`` en 3.9.6 y como ``SyntaxError`` en 3.11.18,
    3.12.16, 3.13.18 y 3.14.8 (medido 25-Nov-2026). Se atrapan los dos porque el tipo
    no es el contrato; dentro de ``>=3.11`` sólo la segunda rama se midió alcanzable.
    """
    try:
        arbol = ast.parse(fuente, filename=ruta)
    except SyntaxError as exc:
        return Fuente(ruta, (), f"sintaxis: {exc.msg}" + (f" (línea {exc.lineno})" if exc.lineno else ""))
    except ValueError as exc:
        return Fuente(ruta, (), f"fuente ilegible: {exc}")
    salida: list[Metodo] = []
    _recorre(arbol.body, "", ruta, salida)
    return Fuente(ruta, tuple(salida))


def metodos(fuente: str, ruta: str = "") -> list[Metodo]:
    """Atajo que ignora el error de lectura. Para veredictos, usar ``leer``."""
    return list(leer(fuente, ruta).metodos)


def nuevos(base: Fuente | None, ref: Fuente) -> list[Metodo]:
    """Métodos de ``ref`` que no existían en ``base``.

    Sin este filtro el predicado dispara sobre todo lo heredado del ancestro
    común: medido, 76 rojos con base global contra 1 con base por pareja.
    """
    if base is None or not base.medida:
        return list(ref.metodos)
    conocidos = {(m.clase, m.nombre) for m in base.metodos}
    return [m for m in ref.metodos if (m.clase, m.nombre) not in conocidos]


def colisiones(a: list[Metodo], b: list[Metodo]) -> list[Colision]:
    """Pares de ``a`` × ``b`` que se pisan al convivir en el mismo archivo.

    No exige que los conjuntos sean disjuntos: ``colisiones(x, x)`` devuelve los
    duplicados internos de ``x``, que es justo lo que deja un merge limpio.
    """
    encontradas: list[Colision] = []
    identicos = a is b
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if x is y or (identicos and j <= i):
                continue
            if x.clave != y.clave:
                if x.ordinal is not None and x.ordinal == y.ordinal and x.nombre != y.nombre:
                    encontradas.append(
                        Colision(AVISO, x, y, f"ordinal {x.ordinal} repetido entre clases distintas")
                    )
                continue
            if x.nombre == y.nombre:
                encontradas.append(Colision(ROJO, x, y, "mismo nombre en la misma clase: el segundo borra al primero"))
            elif x.ordinal is not None and x.ordinal == y.ordinal:
                encontradas.append(Colision(ROJO, x, y, f"ordinal {x.ordinal} en la misma clase, nombre distinto"))
    encontradas.sort(key=lambda c: (c.a.ruta, c.a.clase, c.a.ordinal or 0, c.a.nombre, c.b.nombre))
    return encontradas


@dataclass
class Resultado:
    rojos: list[Colision]
    avisos: list[Colision]
    nuevos_por_rama: dict[str, int]
    ingenuo: int
    no_medidos: list[str]
    motivos: dict[str, str] = field(default_factory=dict)

    @property
    def rc(self) -> int:
        return 1 if self.rojos else 0


def comparar(
    base: dict[str, Fuente],
    ramas: dict[str, dict[str, Fuente]],
    bases_de_par: dict[tuple[str, str], dict[str, Fuente]] | None = None,
) -> Resultado:
    """Veredicto de componer varias ramas sobre una base.

    La base de una pareja no es la base del mundo: ``bases_de_par`` lleva el
    ``git merge-base`` de cada pareja, y lo que dos ramas comparten porque nació
    **después** de la base global es herencia, no duplicado.
    """
    bases_de_par = bases_de_par or {}
    no_medidos: list[str] = []
    motivos: dict[str, str] = {}
    for ruta, f in base.items():
        if not f.medida:
            no_medidos.append(ruta)
            motivos[ruta] = f.error or "sin motivo"
    for ref, archivos in ramas.items():
        for ruta, f in archivos.items():
            if not f.medida:
                clave = f"{ref}/{ruta}"
                no_medidos.append(clave)
                motivos[clave] = f.error or "sin motivo"

    rojos: list[Colision] = []
    avisos: list[Colision] = []
    propios: dict[str, list[Metodo]] = {}
    for ref, archivos in ramas.items():
        lista: list[Metodo] = []
        for ruta, f in archivos.items():
            lista += nuevos(base.get(ruta), f)
        propios[ref] = lista

    for ref, lista in propios.items():
        for c in colisiones(lista, lista):
            rojos.append(Colision(ROJO, c.a, c.b, f"duplicado dentro de {ref}"))

    refs = list(ramas)
    for i, ref_a in enumerate(refs):
        for ref_b in refs[i + 1:]:
            base_par = bases_de_par.get((ref_a, ref_b)) or bases_de_par.get((ref_b, ref_a))
            if base_par is not None:
                solo_a: list[Metodo] = []
                for ruta, f in ramas[ref_a].items():
                    solo_a += nuevos(base_par.get(ruta), f)
                solo_b: list[Metodo] = []
                for ruta, f in ramas[ref_b].items():
                    solo_b += nuevos(base_par.get(ruta), f)
            else:
                solo_a, solo_b = propios[ref_a], propios[ref_b]
            for c in colisiones(solo_a, solo_b):
                (rojos if c.clase == ROJO else avisos).append(c)

    ingenuo = 0
    for i, ref_a in enumerate(refs):
        for ref_b in refs[i + 1:]:
            for ruta, fa in ramas[ref_a].items():
                fb = ramas[ref_b].get(ruta)
                if fb is None:
                    continue
                for x in fa.metodos:
                    for y in fb.metodos:
                        if x.ordinal is not None and x.ordinal == y.ordinal and x.nombre != y.nombre:
                            ingenuo += 1

    return Resultado(rojos, avisos, {r: len(l) for r, l in propios.items()}, ingenuo, no_medidos, motivos)
