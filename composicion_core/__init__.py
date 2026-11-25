"""composicion-core: predicado de composición de ramas y medición con marco declarado."""

from .corpus import Caso, carga, etiqueta
from .marco import MarcoIncompleto, ResultadoMedido
from .ordinal import AVISO, ROJO, Colision, Fuente, Metodo, colisiones, comparar, leer, nuevos, ordinal
from .paridad import Discrepancia, Puntuacion, Sonda, puntuar

__version__ = "0.1.1"

__all__ = [
    "AVISO",
    "Caso",
    "Colision",
    "Discrepancia",
    "Fuente",
    "MarcoIncompleto",
    "Metodo",
    "Puntuacion",
    "ROJO",
    "ResultadoMedido",
    "Sonda",
    "carga",
    "colisiones",
    "comparar",
    "etiqueta",
    "leer",
    "nuevos",
    "ordinal",
    "puntuar",
]
