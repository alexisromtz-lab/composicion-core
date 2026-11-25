"""CLI: puntúa una implementación contra el corpus de conformidad."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from . import __version__, adaptadores
from .corpus import carga
from .paridad import puntuar


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="composicion-core",
        description="Predicado canónico de composición de ramas, y puntuación de herramientas contra él.",
    )
    p.add_argument("--sonda", action="append", default=[], help="core | shadow-guard | governor; repetible")
    p.add_argument("--ruta", action="append", default=[], help="checkout de la herramienta, en el mismo orden que --sonda")
    p.add_argument("--corpus", help="ruta a un corpus alternativo")
    p.add_argument("--casos", action="store_true", help="lista los casos del corpus")
    p.add_argument("--json", action="store_true", help="salida legible por máquina")
    p.add_argument("--self-test", action="store_true", help="puntúa el predicado canónico contra su propio corpus")
    p.add_argument("--version", action="version", version=f"composicion-core {__version__}")
    args = p.parse_args(argv)

    casos = carga(pathlib.Path(args.corpus) if args.corpus else None)

    if args.casos:
        for caso in casos:
            print(f"{caso.id}: {caso.descripcion}")
        return 0

    sondas = ["core"] if (args.self_test or not args.sonda) else args.sonda
    rutas = list(args.ruta)
    puntuaciones = []
    for i, nombre in enumerate(sondas):
        ruta = rutas[i] if i < len(rutas) else str(pathlib.Path.home() / nombre)
        try:
            sonda = adaptadores.cargar(nombre, ruta)
        except (ImportError, SystemExit) as exc:
            print(f"sonda {nombre}: no cargable en {ruta} ({exc})", file=sys.stderr)
            return 2
        puntuaciones.append(puntuar(sonda, casos))

    if args.json:
        print(json.dumps([q.como_dict() for q in puntuaciones], ensure_ascii=False, indent=2))
    else:
        for q in puntuaciones:
            for linea in q.lineas():
                print(linea)
        if args.self_test:
            total = sum(sum(q.acuerdos.values()) for q in puntuaciones)
            print(f"SELF-TEST {'OK' if all(q.rc == 0 for q in puntuaciones) else 'ROTO'}: {total} acuerdos sobre {len(casos)} casos")

    return 0 if all(q.rc == 0 for q in puntuaciones) else 1


if __name__ == "__main__":
    raise SystemExit(main())
