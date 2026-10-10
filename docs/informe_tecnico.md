# Informe técnico

**Autor:** Alberto Orlando Paredes Mamani  
**Repositorio:** https://github.com/alberthP-M/food-ai

## 1. Problema y objetivo

Los menús digitales tradicionales obligan al cliente a navegar por categorías, leer descripciones y aplicar filtros manuales. Esta experiencia es lenta cuando el cliente tiene restricciones dietéticas, alergias, preferencias de sabor o un presupuesto concreto.

El objetivo es implementar un sistema que reciba una solicitud en lenguaje natural, por texto o voz, y devuelva los tres platos disponibles más relevantes, respetando las restricciones registradas del restaurante.

La pregunta experimental es:

> ¿La recuperación semántica de platos mejora la precisión de las primeras recomendaciones frente a una búsqueda tradicional ordenada por popularidad?

## 2. Alcance funcional

La demostración incluye:

- Entrada escrita desde el frontend.
- Entrada por voz en navegadores compatibles.
- Extracción de preferencias y restricciones básicas en español.
- Filtro obligatorio de alérgenos, disponibilidad, dietas, precio y picante.
- Recuperación mediante embeddings multilingües.
- Recomendación de los tres primeros platos.
- Explicación basada en los atributos reales del catálogo.
- Integración de la selección con una simulación de carrito.
- API documentada y pruebas automatizadas.

El envío real de pagos, la gestión completa de usuarios y la operación de cocina quedan fuera del alcance de esta entrega.

## 3. Unidad de observación y línea base

La unidad de observación es cada par formado por una consulta del cliente y un plato elegible del menú.

La línea base filtra los mismos platos no disponibles o incompatibles y los ordena por la columna `popularity`. Esto evita favorecer al sistema inteligente con candidatos que la línea base no podría mostrar.

## 4. Dataset y preparación

El dataset es sintético y se genera con una semilla fija. El catálogo contiene 80 platos con nombre, descripción, ingredientes, alérgenos, dietas, precio, disponibilidad, picante, calorías, proteína, tiempo de preparación y popularidad.

La preparación realiza:

1. Lectura del CSV.
2. Separación de etiquetas y listas de ingredientes.
3. Normalización de consultas para reconocer acentos y expresiones frecuentes.
4. Conversión de restricciones a una estructura de consulta.
5. Construcción de un texto enriquecido por plato.
6. Codificación del texto de cada plato mediante el modelo multilingüe.

El archivo JSONL contiene 100 consultas anotadas. Se separan en 20 consultas de ajuste, 20 de validación y 60 de prueba. Las cinco consultas de “no existe coincidencia segura” se prueban operacionalmente, pero no se usan para calcular Precision@3.

## 5. Modelo

Se usa `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, un modelo preentrenado multilingüe ejecutado mediante FastEmbed y ONNX Runtime. No se realiza fine-tuning en esta entrega.

El índice implementa recuperación semántica sobre el contexto estructurado del menú:

1. El texto de cada plato se transforma en embedding.
2. La consulta se transforma con el mismo encoder.
3. Las reglas eliminan candidatos incompatibles.
4. Se calcula similitud coseno entre la consulta y los candidatos.
5. Se combinan similitud semántica, coincidencia estructurada y popularidad mediante un reordenamiento híbrido.
6. Se devuelven los tres primeros resultados.

No se utiliza un chat generativo: la parte de Machine Learning es el encoder multilingüe preentrenado y la similitud vectorial. Las reglas estructuradas se mantienen separadas para priorizar la seguridad de alergias y disponibilidad.

Los pesos iniciales se compararon sobre el split de validación. La mejor combinación fue:

| Componente | Peso |
|---|---:|
| Similitud semántica | 0.55 |
| Coincidencia estructurada | 0.25 |
| Popularidad | 0.20 |

El script `backend/scripts/tune_weights.py` documenta las combinaciones probadas en `backend/artifacts/weight_search.json`.

El fallback TF-IDF permite ejecutar pruebas sin descargar el modelo, pero no es el modelo principal de la entrega.

## 6. Seguridad de restricciones

La IA no decide si un plato es seguro para una alergia. El sistema aplica reglas sobre el catálogo estructurado. Si el catálogo no declara un ingrediente o alérgeno, la respuesta debe ser revisada por el personal.

La IA puede interpretar “sin lactosa” o “alergia al maní”, pero la exclusión final la realiza el filtro determinista. De esta manera, el modelo no puede reintroducir un plato inseguro por una similitud semántica alta.

## 7. Evaluación

La métrica principal es Precision@3. Para cada consulta se comparan los tres identificadores recomendados con `relevant_ids`.

```text
Precision@3 = platos relevantes en los tres primeros resultados / 3
```

Se reportan:

- Precision@3 del sistema semántico.
- Precision@3 de la línea base.
- Resultados por consulta.
- Casos en los que no existen candidatos.

Resultado reproducible con el modelo FastEmbed sobre el split de prueba ampliado:

| Split | Consultas puntuadas | Sistema | Precision@3 |
|---|---:|---|---:|
| Validación | 20 | Pesos seleccionados | 0.6167 |
| Prueba | 55 | Línea base: filtros + popularidad | 0.6121 |
| Prueba | 55 | Recomendador híbrido | 0.4727 |

La línea base supera al modelo en este conjunto pequeño. Esto se reporta sin ocultarlo: muestra que las anotaciones y el ranking semántico todavía deben ampliarse con consultas reales y una etapa de reordenamiento supervisado. La entrega se evalúa por la comparación honesta, la trazabilidad y el flujo funcional, no por afirmar una mejora inexistente.

La evaluación no ajusta el modelo con las consultas finales. Si el sistema se amplía con entrenamiento supervisado, se deberá separar consultas de entrenamiento, validación y prueba, evitando que la misma consulta o el mismo registro relacionado aparezca en particiones distintas.

## 8. Backend

El backend usa FastAPI. Endpoints principales:

- `GET /api/health`
- `GET /api/ready`
- `GET /api/menu`
- `POST /api/recommend`
- `POST /api/feedback`
- `GET /api/evaluation`

El endpoint de recomendación valida longitud, canal y cantidad de resultados. Maneja consultas sin coincidencias y devuelve un mensaje claro. `/api/ready` permite distinguir entre el backend iniciado y el modelo listo para inferencia.

## 9. Frontend

El frontend es una interfaz estática servida por Nginx. Permite:

- Escribir una consulta.
- Dictarla mediante Web Speech API.
- Seleccionar el canal de demostración.
- Ver las restricciones detectadas.
- Revisar las tres recomendaciones.
- Mostrar los pesos del ranking en la respuesta de la API.
- Leer precio, ingredientes, tiempo y explicación.
- Simular la acción “Agregar al carrito”.
- Ver estados de carga y errores.

## 10. Pruebas realizadas

La suite cubre:

- Extracción de dieta, alérgenos, precio, picante y proteína.
- Respeto de filtros de seguridad.
- Respuesta sin candidatos seguros.
- Comparación con línea base.
- Health check de la API.
- Consulta válida.
- Consulta inválida.

La última ejecución produjo 12 pruebas automáticas exitosas. Además, el flujo Docker se validó con un healthcheck que espera a que `/api/ready` responda correctamente.

### Tabla de errores

| Tipo | Consulta | Resultado observado | Lectura técnica |
|---|---|---|---|
| Acierto del modelo | “Busco fideos con verduras” | Recupera noodles con tofu, pasta vegetal y pasta con garbanzos | La semántica encuentra platos aunque la palabra exacta no sea “pasta” en todos los nombres. |
| La base supera al modelo | “Sin gluten y sin soya” | La base prioriza platos populares compatibles | El embedding conserva candidatos semánticamente parecidos, pero el ranking de popularidad ordena mejor este caso. |
| Caso de seguridad | “Alergia a pescado y quiero salmón” | No devuelve recomendaciones | El filtro determinista bloquea la contradicción y evita recomendar un plato inseguro. |

La demostración manual debe mostrar un caso válido, un caso difícil y una entrada inválida.

## 11. Limitaciones

- El dataset es sintético y las consultas no representan todavía clientes reales.
- La línea base supera al modelo en el conjunto de prueba actual.
- El sistema aún no aprende preferencias personales a partir de historial real.
- No se entrena un modelo con historial real de clientes.
- El reconocimiento de voz depende del navegador.
- El sistema no ofrece consejo médico.
- La exactitud de las restricciones depende del catálogo ingresado por el restaurante.

## 12. Conclusión

El sistema demuestra un flujo completo de Machine Learning aplicado a un caso de uso de restaurante: entrada de datos, preparación, recuperación semántica, filtrado de seguridad, recomendación, evaluación, API y frontend.

El resultado es una base funcional que puede evolucionar con un menú real, consultas reales anonimizadas y una etapa posterior de personalización basada en historial.
