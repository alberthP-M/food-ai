# Guion de presentación individual: 5 minutos

**Autor:** Alberto Orlando Paredes Mamani  
**Repositorio:** https://github.com/alberthP-M/food-ai

## Diapositiva 1 — Problema y solución (45 segundos)

Los clientes deben navegar manualmente por menús digitales y les cuesta encontrar platos compatibles con sus preferencias o alergias. La solución recibe texto o voz y recomienda tres platos disponibles.

## Diapositiva 2 — Dataset, línea base y modelo (60 segundos)

- Dataset sintético reproducible: 80 platos y 100 consultas anotadas.
- Separación: 20 para ajuste, 20 para validación y 60 para prueba.
- Línea base: filtros manuales y popularidad.
- Modelo: embeddings multilingües y recuperación semántica.
- Ranking híbrido validado: 55% semántica, 25% restricciones y 20% popularidad.
- Restricciones de alergias: reglas deterministas antes del ranking.
- Métrica: Precision@3.

## Diapositiva 3 — Resultado principal (45 segundos)

Mostrar la tabla generada por `python scripts/evaluate.py`:

| Sistema | Precision@3 |
|---|---:|
| Línea base: filtros + popularidad | 0.6121 |
| Modelo híbrido | 0.4727 |

Explicar una consulta donde el modelo encuentre platos por significado, aunque las palabras no coincidan exactamente. Aclarar que la línea base gana en este dataset sintético y que la comparación se presenta de forma honesta.

## Diapositiva 4 — Demostración (2 minutos)

1. Abrir <http://localhost:8080>.
2. Escribir: “Quiero algo vegetariano, sin lactosa y poco picante”.
3. Mostrar las condiciones detectadas.
4. Mostrar las tres recomendaciones.
5. Probar: “Busco algo sin gluten con pollo y menor a Bs 50”.
6. Probar una consulta sin coincidencias seguras: “Alergia a pescado y quiero salmón”.
7. Probar una entrada inválida.
8. Si el navegador lo permite, repetir una consulta con el botón de voz.

## Diapositiva 5 — Conclusión, limitaciones y repositorio (30 segundos)

La entrega implementa el flujo completo desde la consulta hasta la recomendación visible. Sus limitaciones principales son el dataset sintético, el número reducido de consultas y la dependencia de la calidad del catálogo de alérgenos. Mostrar el enlace del repositorio y explicar cómo ejecutarlo con Docker.
