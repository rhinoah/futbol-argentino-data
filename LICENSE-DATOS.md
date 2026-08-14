# Licencia de los datos

El **código** de este repositorio está bajo licencia MIT (ver [`LICENSE`](LICENSE)).

Los **datos** (`data/partidos.csv`) no, y no pueden estarlo: son una obra derivada
de Wikipedia en español, así que heredan su licencia.

## Creative Commons Atribución-CompartirIgual 4.0 (CC BY-SA 4.0)

- Texto completo: https://creativecommons.org/licenses/by-sa/4.0/legalcode.es
- Resumen: https://creativecommons.org/licenses/by-sa/4.0/deed.es

Podés **usarlos, copiarlos, modificarlos y redistribuirlos, incluso
comercialmente**, con dos condiciones:

1. **Atribución.** Hay que decir de dónde salen. La columna `source` de cada fila
   trae la URL exacta de la página de la que se extrajo ese partido, así que la
   atribución viaja con el dato y no depende de que alguien lea este archivo.
2. **CompartirIgual.** Si publicás una versión modificada del dataset, va con la
   misma licencia.

## Atribución sugerida

> Datos extraídos de [Wikipedia en español](https://es.wikipedia.org), disponibles
> bajo [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.es), vía
> [futbol-argentino-data](https://github.com/rhinoah/futbol-argentino-data).

## Por qué Wikipedia y no una API

Las alternativas obvias — las APIs de resultados deportivos — tienen datos mejor
estructurados y **términos de uso que prohíben redistribuirlos**. Sirven para
consultar, no para armar un dataset y publicarlo. Wikipedia es la única fuente
con cobertura del ascenso argentino cuya licencia permite justamente esto.

Es la razón por la que el parser existe en vez de un `requests.get` a un endpoint
JSON: el laburo de sacar los partidos del wikitexto es el precio de poder
compartir el resultado.


## Una segunda fuente, para un solo campo

La **fecha del calendario** de algunos partidos del ascenso 2004-2010 no está en
Wikipedia: esas páginas publican los resultados en tablas de tres columnas, sin
fecha. Ese campo, y sólo ese, se completa consultando
[worldfootball.net](https://www.worldfootball.net/).

La columna `source` de esas filas nombra las dos fuentes. Todo lo demás de la
fila —equipos, marcador, jornada, estadio— viene de Wikipedia y está cubierto
por CC BY-SA.

Sus términos de uso limitan el aprovechamiento a fines personales y no
comerciales. Este proyecto no persigue ninguno. Si worldfootball considera que
ese aporte no corresponde, alcanza con [abrir un
issue](https://github.com/rhinoah/futbol-argentino-data/issues) y se retira: los
partidos quedan igual, sin la fecha.
