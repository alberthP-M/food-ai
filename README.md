# Food AI Recommender

Sistema funcional de búsqueda y recomendación de platos para un POS de restaurante. El usuario escribe o dicta una solicitud en español, el backend interpreta sus preferencias, aplica restricciones de seguridad, recupera los platos más relacionados semánticamente y devuelve las tres mejores opciones.

El proyecto está pensado como entrega final de Machine Learning. Incluye dataset sintético reproducible, ajuste de pesos con validación, modelo de embeddings, línea base, evaluación, API, frontend, pruebas, Docker e informe técnico.

## Repositorio

Código fuente y entregables:

<https://github.com/alberthP-M/food-ai>

## Inicio rápido en otra PC

La forma recomendada de ejecutar el sistema es con Docker. No es necesario instalar
Python, Node.js ni las dependencias del modelo.

### Requisitos

- Git.
- Docker Desktop abierto y funcionando.
- Conexión a Internet durante el primer arranque para descargar el modelo.

### Instalación y ejecución

En una terminal, ejecuta:

```bash
git clone https://github.com/alberthP-M/food-ai.git
cd food-ai
docker compose up --build -d
```

Espera a que el backend termine de cargar el modelo y verifica su estado:

```bash
docker compose ps
curl http://localhost:8000/api/ready
```

La respuesta debe incluir `"status":"ready"`. Después abre:

- Aplicación: <http://localhost:8080>
- Documentación de la API: <http://localhost:8000/docs>
- Estado del backend: <http://localhost:8000/api/health>

El primer arranque puede tardar porque descarga el modelo multilingüe. En los
siguientes arranques Docker reutiliza la caché.

### Detener o reiniciar

```bash
docker compose down
docker compose up -d
```

Si Docker informa que los puertos `8080` o `8000` ya están ocupados, libera esos
puertos o modifica la sección `ports` de `docker-compose.yml`.

## Objetivo

Resolver la tarea:

> Dada una consulta de un cliente y el catálogo vigente del restaurante, recuperar y ordenar los platos compatibles más relevantes.

Ejemplo:

> “Quiero algo vegetariano, sin lactosa, poco picante y menor a Bs 50.”

La aplicación separa las responsabilidades:

- Las restricciones de alergias, disponibilidad y catálogo se validan con reglas deterministas.
- El modelo de Machine Learning interpreta la consulta y recupera los platos semánticamente más relevantes.
- La API devuelve las tres primeras recomendaciones y una explicación basada en datos del menú.

## Arquitectura

```text
Frontend web / kiosko
        │ POST /api/recommend
        ▼
FastAPI
        │
        ├── Parser de consulta en español
        ├── Filtro obligatorio de alérgenos y disponibilidad
        ├── Índice de embeddings del menú
        ├── Recuperación semántica y reordenamiento híbrido top-3
        └── Respuesta estructurada para la interfaz
        │
        ▼
Catálogo CSV + artefacto de embeddings
```

La entrada por voz usa Web Speech API en el navegador y convierte el audio en texto antes de llamar al mismo endpoint. La voz es un canal de entrada; el componente inteligente evaluado es la comprensión y recuperación de platos.

## Modelo

El modelo principal es:

```text
Recuperación semántica con embeddings multilingües del menú
Modelo: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 mediante FastEmbed/ONNX Runtime
Pesos seleccionados en validación: 55% semántica, 25% restricciones y 20% popularidad
```

El modelo preentrenado se reutiliza sin fine-tuning. Se documenta su origen mediante el identificador de Hugging Face y su configuración. El sistema codifica cada plato y la consulta como vectores, calcula similitud coseno y ordena los candidatos seguros.

La respuesta no depende de una API externa ni de respuestas escritas de antemano. Las explicaciones se construyen con los atributos reales del catálogo para evitar inventar precios, ingredientes o disponibilidad.

En pruebas locales sin descarga del modelo se puede usar `MODEL_BACKEND=tfidf`. Ese modo es un fallback técnico para pruebas, no el modelo principal que debe presentarse en la evaluación final.

## Línea base y métrica

### Línea base

La línea base ordena los platos compatibles por popularidad histórica del menú. Usa exactamente los mismos filtros de disponibilidad y seguridad que el sistema inteligente.

### Métrica principal

`Precision@3`:

```text
cantidad de platos relevantes dentro de las tres primeras recomendaciones / 3
```

La relevancia está anotada en `backend/data/evaluation_queries.jsonl`. La comparación final usa únicamente el split de prueba. Las consultas de ajuste y validación no se mezclan con la prueba.

Resultado de la última evaluación reproducible:

| Split | Consultas | Sistema | Precision@3 |
|---|---:|---|---:|
| Validación | 20 | Pesos seleccionados | 0.6167 |
| Prueba | 55 | Recomendador híbrido | 0.4727 |
| Prueba | 55 | Línea base | 0.6121 |

Las cinco consultas de “no existe coincidencia segura” se validan como pruebas operativas de seguridad y no se mezclan con la métrica de ranking. La línea base todavía supera al modelo en este dataset sintético; el informe presenta los errores y la comparación completa sin ocultar ese resultado.

La evaluación actual utiliza el split de prueba ampliado. El resultado anterior de 12 consultas pertenece a la primera versión del prototipo y se conserva únicamente en el historial de Git, no como resultado vigente.

## Dataset

El dataset incluido es sintético y reproducible porque el restaurante todavía no dispone de un historial público de pedidos.

- Generador: `backend/scripts/generate_dataset.py`
- Semilla: `20261010`
- Menú: 80 platos
- Consultas anotadas: 100
- Ajuste: 20 consultas
- Validación: 20 consultas
- Prueba: 60 consultas, 55 puntuadas y 5 casos de seguridad
- Variables de menú: nombre, descripción, categoría, precio, dietas, alérgenos, ingredientes, picante, disponibilidad, tiempo de preparación, calorías, proteína y popularidad.
- Anotaciones: identificadores de platos relevantes para cada consulta.

El dataset sintético sirve para demostrar el flujo funcional, pero no representa el comportamiento definitivo de clientes reales. La siguiente versión debe sustituir o ampliar las consultas con interacciones reales, con autorización y sin datos personales innecesarios.

## Ejecución local

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_dataset.py
MODEL_BACKEND=fastembed python scripts/build_index.py
MODEL_BACKEND=fastembed python scripts/tune_weights.py
MODEL_BACKEND=fastembed python scripts/evaluate.py
uvicorn app.main:app --reload --port 8000
```

En otra terminal, servir el frontend estático:

```bash
cd frontend
python3 -m http.server 8080
```

## Pruebas

Las pruebas automáticas usan el fallback TF-IDF para evitar descargar el modelo durante CI:

```bash
cd backend
MODEL_BACKEND=tfidf pytest -q
```

La demostración manual debe cubrir:

1. **Caso válido:** `Quiero algo vegetariano, sin lactosa, poco picante.`
2. **Caso difícil:** `Busco algo sin gluten con pollo, menor a Bs 50.`
3. **Entrada inválida:** texto de un carácter o consulta vacía.
4. **Caso sin coincidencia segura:** `Alergia a pescado y quiero salmón.`
5. **Caso de voz:** usar el botón “Hablar” en un navegador compatible.

## API

### Salud del servicio

```bash
curl http://localhost:8000/api/health
```

### Preparación del modelo

```bash
curl http://localhost:8000/api/ready
```

`/api/health` puede responder `loading` mientras el modelo no se inicializa. `/api/ready` responde cuando el encoder y el índice están disponibles.

### Recomendación

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"query":"Quiero algo vegetariano, sin lactosa y poco picante","top_k":3,"channel":"kiosk"}'
```

### Evaluación

```bash
curl http://localhost:8000/api/evaluation
```

### Feedback

```bash
curl -X POST http://localhost:8000/api/feedback \
  -H 'Content-Type: application/json' \
  -d '{"query":"algo vegano","dish_id":"bowl-quinoa","action":"click","channel":"web"}'
```

## Estructura

```text
backend/
  app/                  API, parser, catálogo, modelo y evaluación
  data/                 menú y consultas anotadas
  scripts/              generación, indexación, ajuste y evaluación
  tests/                pruebas unitarias y de API
  artifacts/            índice y resultados generados
frontend/               interfaz web estática
docs/
  informe_tecnico.md    informe base para convertir a PDF
  build_reference_style_report_pdf.py  generador del informe PDF final
  presentacion_5_min.md guion de presentación individual
  dataset_card.md       ficha del dataset
  screenshots/           evidencia visual del flujo real
output/pdf/informe_tecnico_final.pdf
output/presentation/presentacion_5_min_final.pptx
docker-compose.yml
```

El informe PDF final incluye capturas obtenidas ejecutando el frontend conectado al
backend real: caso válido, consulta difícil, caso sin coincidencias seguras y
entrada inválida.

## Limitaciones y alcance

- La aplicación no sustituye la confirmación del personal ante una alergia severa.
- Un alérgeno desconocido no debe tratarse como ausencia de alérgenos.
- La calidad depende de que el administrador mantenga ingredientes y alérgenos actualizados.
- El historial del cliente es una extensión; la primera versión funciona sin historial.
- El modelo no realiza consejos médicos ni calcula dietas clínicas.
- El catálogo es sintético para la demostración y debe reemplazarse por datos autorizados para una evaluación operativa.
- El reconocimiento de voz depende del navegador y puede no estar disponible en todos los entornos.

## Referencias pedagógicas

La solución sigue el patrón de los ejemplos docentes `semantic-rag-demo` y `product-recommender-demo` indicados en el LMS. Los archivos requieren autenticación institucional, por lo que esta implementación no depende de descargarlos durante la ejecución.
