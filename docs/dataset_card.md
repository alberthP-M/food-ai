# Ficha del dataset

## Identificación

- **Nombre:** Food AI Menu Synthetic Dataset.
- **Tipo:** sintético.
- **Generador:** `backend/scripts/generate_dataset.py`.
- **Semilla:** `20261010`.
- **Tamaño:** 80 platos y 100 consultas anotadas.

## Propósito

Evaluar un sistema de recuperación y recomendación semántica de platos para consultas de clientes en español.

## Variables de los platos

| Variable | Descripción |
|---|---|
| `id` | Identificador estable del plato. |
| `name` | Nombre comercial. |
| `description` | Descripción breve. |
| `category` | Categoría del menú. |
| `price` | Precio en bolivianos. |
| `diet_tags` | Etiquetas dietéticas separadas por punto y coma. |
| `allergens` | Alérgenos conocidos. |
| `ingredients` | Ingredientes registrados. |
| `spice_level` | Nivel `low`, `medium` o `high`. |
| `available` | Disponibilidad actual del plato. |
| `prep_minutes` | Tiempo estimado de preparación. |
| `calories` | Calorías estimadas. |
| `protein_g` | Proteína estimada en gramos. |
| `popularity` | Señal sintética para la línea base. |

## Consultas de evaluación

Cada línea de `evaluation_queries.jsonl` contiene:

- `id`: identificador de la consulta.
- `query`: texto en español.
- `relevant_ids`: platos relevantes anotados para Precision@3.
- `split`: `tuning`, `validation` o `test`.
- `scored`: indica si la consulta participa en Precision@3.

Las consultas se separan por grupos de intención para evitar que variaciones casi idénticas aparezcan en splits diferentes. Hay 20 consultas para ajuste, 20 para validación y 60 para prueba. Cinco consultas de prueba verifican que el sistema rechace solicitudes incompatibles con alergias y no se incluyen en la métrica de ranking.

El modelo preentrenado se usa sin fine-tuning. La validación solo ajusta los pesos del reordenamiento híbrido; la prueba final no se usa para elegirlos.

## Limitaciones

Los datos sintéticos no modelan toda la variedad lingüística ni el comportamiento de clientes reales. Las etiquetas y anotaciones son pequeñas y didácticas. Para una versión de investigación ampliada se deben recolectar consultas y decisiones reales con consentimiento, anonimizarlas y separar consultas de evaluación antes de ajustar cualquier reranker.
