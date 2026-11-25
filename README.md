# composicion-core

Predicado canónico para una pregunta que `git merge` no contesta: **¿dos ramas
declaran el mismo test?**

`git merge-tree` compara texto. Cuando dos ramas insertan `def test_algo` en
rangos de línea distintos, no hay conflicto textual: el merge entra limpio, el
archivo acaba con dos `def test_algo` y Python conserva uno. El CI queda en
verde **con un test menos**.

Este paquete es el predicado, el corpus que lo fija y el contrato de medición
que impide publicar una cifra sin su marco.

## Qué trae

| pieza | qué hace |
|---|---|
| `composicion_core.ordinal` | `leer()` · `metodos()` · `nuevos()` · `colisiones()` · `comparar()` — tres reglas, un veredicto |
| `composicion_core.marco` | `ResultadoMedido`: una deuda sin base y techo **no se puede construir** |
| `composicion_core.corpus` | 12 casos ejecutables que declaran qué canales afirman y cuántos lados tienen |
| `composicion_core.paridad` | puntúa cualquier herramienta contra el corpus y separa discrepancia de *no comparable* |
| `composicion_core.adaptadores` | sondas listas para `py-test-shadow-guard` y `merge-lattice-governor` |

Cero dependencias. `python >= 3.11`.

```console
$ uvx --from composicion-core composicion-core --self-test
composicion-core: 10 rojo · 10 aviso · 10 no_medido · 0 discrepancias · 0 no comparables
SELF-TEST OK: 30 acuerdos sobre 12 casos
```

## Las tres reglas

1. **Misma clase, mismo nombre.** `ROJO`. Python sobrescribe el método: se pierde
   un test. No es una convención, es el diccionario de la clase.
2. **Misma clase, mismo ordinal, nombre distinto.** `ROJO`. No se pierde ningún
   test: los dos corren. Se marca porque el número es el mecanismo con el que
   varios autores —o varios agentes— se coordinan, y tras el merge dos creen ser
   dueños del 35.
3. **Clases distintas, mismo ordinal.** `AVISO`. No rompe la ejecución; degrada
   la trazabilidad.

Los dos primeros son `ROJO` por razones distintas y conviene no confundirlas:
el primero por **semántica de Python**, el segundo por **convención del
proyecto**.

## El corpus, y lo que mide de verdad

Los 12 casos incluyen el canario real: dos ramas, 19 tests heredados del
ancestro común y una colisión intra-clase. El predicado ingenuo —comparar
ordinales entre ramas— dispara **20** veces. El discriminado —misma clase,
mismo ordinal, nombre distinto, ambos nuevos respecto de la base— dispara **1**.

Medido el 25-Nov-2026 contra los dos paquetes hermanos:

| herramienta | rojo | aviso | no_medido | discrepancias | no comparables |
|---|---|---|---|---|---|
| `composicion-core` | 10 | 10 | 10 | 0 | 0 |
| `py-test-shadow-guard` 0.1.2 | 10 | 10 | 10 | 0 | 0 |
| `merge-lattice-governor` 0.1.2 | 9 | 9 | 9 | 0 | 1 |

La única fila no comparable del gobernador no es un verde: es su contrato,
publicado. **No emite canal de avisos** —el aviso global de ordinal compartido
entre clases distintas—, así que el juez no tiene dónde puntuarlo. Los otros
tres huecos que declaraba la versión 0.1.1 (auditar una rama sola, publicar
`NO_MEDIDO` y detectar un duplicado interno de la propia rama) están cerrados y
el juez los puntúa: 4 → 1.

## Contrato de marco declarado

```python
>>> from composicion_core.marco import ResultadoMedido
>>> ResultadoMedido(valor=-721, clase="delta", universo="origin/main", base="34ee1d2c")
MarcoIncompleto: delta sin techo: la cifra no es interpretable
```

Nació de tres errores del mismo día en el mismo repositorio: una deuda leída
como holgura, una base global usada donde hacía falta `git merge-base` por
pareja (`76 → 1`), y una masa medida contra el *tip* en vez de contra su base
(`−721` contra `277`). Los tres tienen la misma forma: **una cifra sin su
marco**. Aquí no se puede escribir.

`NO_MEDIDO` (`valor=None`) exige `rc != 0`: nunca se degrada a cero.

## Límites declarados

1. Working tree, no historia: lee archivos, no un repositorio. La parte git la
   pone quien lo llama (los dos paquetes hermanos).
2. Un archivo que no compila es `NO_MEDIDO`, nunca "cero métodos". En 3.11 un
   byte nulo llega como `ValueError` en 3.9.6 y como `SyntaxError` en 3.11.18,
   3.12.16, 3.13.18 y 3.14.8 (medido 25-Nov-2026, también en el log de CI); se
   atrapan las dos, y dentro de `>=3.11` sólo la segunda se midió alcanzable.
3. Sólo `def test*` con `ast`. Un test generado por metaprogramación no se ve.
4. El corpus fija el predicado, no el gusto de cada proyecto: un equipo que
   numere distinto debe cambiar el corpus, no el código, y decirlo.
5. Una pareja sin base no distingue herencia de colisión: `nuevos(base=None)`
   devuelve todo. El ruido es entonces del llamador, no del predicado.
6. No mide cobertura ni correctitud: mide que dos métodos no se pisen.
7. `rc` es 0/1/2. Un 2 es *no medido*, no *verde*.

## Uso

```console
$ composicion-core                                  # 12 casos contra el propio núcleo
$ composicion-core --sonda shadow-guard --ruta /ruta/al/checkout
$ composicion-core --sonda governor --ruta /ruta/al/checkout --json
```

## Familia

- [py-test-shadow-guard](https://github.com/alexisromtz-lab/py-test-shadow-guard) — el defecto en una pareja de ramas.
- [merge-lattice-governor](https://github.com/alexisromtz-lab/merge-lattice-governor) — el orden en que N ramas pueden aterrizar sin romperse.

MIT © 2026 Platino Labs.
