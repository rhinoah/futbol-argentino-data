# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 44 027 | 10 | 149 | 948 | 392 |

## 2004–2026 — Cerrado

`41 558` partidos y no falta ninguno. De los `181` avisos —cero graves— `94` son
informativos y `17` son ciertos y no cierran nunca; los dos grupos tienen su explicación
en el archivo que los produce y no se repiten acá. Lo que queda:

- **Dos fuentes que no coinciden.** `60` partidos con dos días distintos en 9 páginas, y
  `6` con dos marcadores. Se conserva el de la página y se avisa. Cerrarlo pide una
  tercera fuente, o una regla de precedencia que hoy no está medida.
- **`10` partidos sin fecha, y sólo `4` esperan una.** Los otros `6` no se jugaron —los
  que el Federal A 2024 le dio por perdidos a Sansinena—. De los 4: dos del `Argentino A
  2004-05` (uno donde la fuente citada le erra al día y otro donde da otro marcador), uno
  con el marcador en disputa y uno de la temporada en curso.
- **`3` tablas que no cierran con su grilla, y las tres son de la temporada en curso.**
  Ninguna es un error de lectura: `San Miguel` (Primera Nacional) desvía un gol, y
  `Real Pilar` (Primera B) y `Muñiz` (Primera C) desvían en G-E-P **con los goles
  coincidiendo exacto**, que es la firma de un fallo y no de un dígito mal leído.
- **Extender la foja de RSSSF**, que es el testigo más fuerte que hay. Ya cruza las 4
  páginas sin grilla; lo que falta es correrla en las que **sí** tienen grilla, donde
  sería un testigo nuevo y gratis de nuestras lecturas de Wikipedia. Ahí falta el mapa
  de nombres por temporada, que es lo caro.
- **Fechar un desacuerdo.** Ningún testigo puede decir *cuándo* la página cambió de
  opinión, y es la deuda más cara. Pide terminar el modelo de la «Evolución de las
  posiciones» —medido dio 12% de desvíos, un modelo incompleto haciendo ruido— o cruzar
  contra una fuente de afuera.

## 1997–2003 — Cerrado

**2 469 partidos, y salieron casi gratis**

Las páginas `Anexo:Torneo Apertura/Clausura AAAA (Argentina)` traen los resultados completos —`190` por torneo, que es veinte clubes todos contra todos— y el parser ya las leía **sin un solo cambio**. Entraron 13 temporadas, del Apertura 1997 al Clausura 2003, con cero graves.

- **Sumar Huracán Corrientes al padrón.** Es el único club de verdad que estos años traen y que no está. Los otros dos nombres desconocidos no son clubes: `Deportivo Maniyú` es la página escribiendo mal `Deportivo Mandiyú`, que ya está, y `Gimnasia J)` es markup roto.

Eran 14 y entraron 13: el Clausura 1997 cae del otro lado de la línea de las fechas y se fue con la capa de abajo.

## 1991–1996 — Lo próximo

**Los partidos están; lo que falta es la fecha**

Esta sección decía «acá se termina Wikipedia» y **estaba equivocada**. Afirmaba que ninguna página de estos años trae sección de resultados, y eso vale para las de temporada pero no para los anexos: el `Anexo:Torneo Apertura 1993` da `190` partidos, 20 clubes con **ninguno desconocido** y 19 fechas de diez exactas. Un todos contra todos perfecto.

Son **2 280** partidos que ya parsean, y **2 270** de ellos **no traen una sola fecha**. Una fila sin fecha no se escribe, así que quedan afuera hasta conseguir de dónde fecharlos.

- **RSSSF publica Primera de estos años.** Es el mismo mecanismo que fechó cinco temporadas del Argentino A esta semana, y la fuente ya está acreditada en el repo.
- El **Clausura 1997** entra acá: de sus 190 partidos, 10 traen fecha.
- **Hueco:** `Anexo:Torneo Clausura 1991` es un stub de 83 bytes. Ese torneo hay que buscarlo en otro lado.
- Fuente candidata para lo que no cubra RSSSF: planillas de la AFA, *Torneos y Certámenes Oficiales 1990-91 … 1994-95*.

El muro se corrió: ya no es «no hay datos» sino «no hay fechas», que es un problema con solución conocida.

## 1985–1990 — Muro

**Mismo muro, misma salida**

Es cuando el campeonato pasa al calendario europeo, agosto a junio, con un solo campeón por temporada. Wikipedia tampoco trae los partidos.

- Planillas AFA *1985-1989* y *Torneos y Certámenes 1990-91*.

## 1967–1984 — El bloque grande

**3 501 partidos que el parser ya lee**

Acá se jugaban **dos torneos por año**: el Metropolitano, con los clubes de AFA, y el Nacional, que sumaba equipos del interior. Por eso el Nacional parsea con zonas *y* eliminación.

- **Campeonato Nacional 1967-1982 — `3 501` partidos con fecha, sin tocar una línea de código.**
- El costo está en el padrón: `544` apariciones de clubes que no conoce —San Lorenzo de Mar del Plata, Atlético Ledesma, Jorge Newbery de Jujuy, Juventud Alianza, Renato Cesarini—. Son 60 a 100 entradas, y `nombres_en_el_padron` es grave, así que van todas antes.
- **Metropolitano** — vive bajo `Campeonato de Primera División AAAA (Argentina)`. 1981 y 1984 parsean (`305` y `342`).
- **Hueco de parser:** 1980, 1982 y 1983 tienen entre 44k y 54k de wikitexto y devuelven `0`.
- **Hueco:** el Nacional de 1983, 1984 y 1985 también da cero.

## 1933–1966 — Sin fuente digital

**Sólo planillas**

Wikipedia no tiene los partidos y no hay otra fuente estructurada identificada. Todo depende de la biblioteca de la AFA.

- **Hueco de la propia biblioteca:** **1964 a 1968** no está digitalizado. Entre las planillas 1955-1963 y las 1969-1973 no hay nada.
