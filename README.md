# AI Workflow Automation System 

Sistema de automatización de procesos de negocio impulsado por IA que elimina tareas manuales y repetitivas, procesa inputs no estructurados (emails, documentos, formularios) y los transforma en acciones concretas mediante un agente de IA.

---

## Features

- **Ingesta multi-fuente** — acepta input de email, formulario, PDF, API o ingreso manual
- **Clasificación automática** — detecta el tipo de proceso (invoice, lead, claim, support ticket, payment request, etc.)
- **Extracción estructurada** — extrae campos relevantes: nombre, email, monto, fecha, número de orden
- **Validación y confidence scoring** — asigna un score (0–100) que determina el ruteo automático
- **Ruteo inteligente** — alta confianza → ejecución automática; baja confianza o alto riesgo → cola de revisión humana
- **Reglas de negocio** — montos por encima del umbral configurado y ciertos tipos de acción siempre requieren aprobación manual
- **Human-in-the-loop** — cola de aprobaciones con formulario de reviewer, notas y trazabilidad
- **Audit trail inmutable** — cada evento del pipeline queda registrado con timestamp y actor
- **Dashboard en tiempo real** — métricas clave, gráficos de volumen, tabla de procesos y cola de aprobaciones
- **Modo dual (LLM Opcional)**: puede operar con modelos de lenguaje para mejorar la comprensión o funcionar completamente con reglas sin depender de APIs externas

---

## Arquitectura

El agente procesa cada input a través de un pipeline secuencial:

```
Input
  └── Classify      → determina el tipo de proceso
        └── Extract   → extrae campos estructurados
              └── Validate  → verifica campos requeridos y formatos
                    └── Confidence Score  → pondera resultado del pipeline
                          └── Decide      → aplica reglas de negocio
                                └── Execute / Escalate
                                      ├── Alta confianza → auto-execute → Audit Log
                                      └── Baja confianza o alto riesgo → Approval Queue → Audit Log
```

### Reglas de escalación

- Monto superior al umbral (`HIGH_VALUE_THRESHOLD`)
- Acciones de alto riesgo (ej: payment request)
- Bajo confidence score
- Múltiples errores de validación

---

## Tech Stack

**Backend**
- Python + FastAPI — API REST asíncrona con documentación OpenAPI automática
- SQLAlchemy 2.0 — ORM con SQLite (desarrollo) / PostgreSQL (producción)
- Pydantic v2 — validación de schemas y configuración con variables de entorno
- LLM integration (opcional) — clasificación y extracción con modelos de lenguaje
- Alembic — migraciones de base de datos

**Frontend**
- React 18 + TypeScript — UI tipada end-to-end
- Vite — build tool y servidor de desarrollo
- Tailwind CSS — estilos utilitarios
- TanStack Query — gestión de estado del servidor
- Recharts — visualización de métricas
- Axios — cliente HTTP 

**Infraestructura**
- Docker + Docker Compose — contenedores para backend y frontend
- SQLite (dev) / PostgreSQL (prod)

---

## Estructura del proyecto

```
ai-workflow-automation-agent/
├── backend/
│   ├── app/
│   │   ├── agent/              # Módulos del pipeline
│   │   │   ├── pipeline.py         # Orquestador principal
│   │   │   ├── classifier.py       # Clasificación por tipo
│   │   │   ├── extractor.py        # Extracción de campos
│   │   │   ├── validator.py        # Validación + confidence scoring
│   │   │   ├── decision_engine.py  # Reglas de negocio y ruteo
│   │   │   └── action_executor.py  # Ejecución simulada de acciones
│   │   ├── api/routes/         # Endpoints REST
│   │   ├── db/                 # Modelos ORM y sesión de base de datos
│   │   ├── schemas/            # Schemas Pydantic
│   │   ├── services/           # AI service 
│   │   └── core/               # Configuración y logging
│   ├── scripts/
│   │   └── seed_data.py        # Generador de datos de demostración
│   ├── tests/                  # Tests de integración del pipeline
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/              # Dashboard, Processes, Approvals, Metrics, NewProcess
│       ├── components/         # StatusBadge, ConfidenceBar, Timeline, MetricCard, etc.
│       ├── api/                # Cliente HTTP 
│       └── types/              # Interfaces TypeScript compartidas
├── docker-compose.yml
└── start.bat                   # Launcher para Windows
```

---

## Cómo ejecutar el proyecto

### Requisitos previos
- Python 3.10+
- Node.js 18+

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env           # Configurar variables de entorno
python -m scripts.seed_data    # Cargar datos de demostración (opcional)
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Accesos

| Servicio | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| API Docs (Swagger) | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### Docker (alternativa)
```bash
docker-compose up --build
```

### Windows (launcher rápido)
```bash
start.bat
```

---

## Flujo de uso

**1. Enviar un input**

Ir a la sección **New Process** en el dashboard o usar la API directamente:

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/submit \
  -H "Content-Type: application/json" \
  -d '{
    "source": "email",
    "raw_input": "From: vendor@acme.com\nInvoice #INV-2024-001 — $4,500 due November 15\nPlease process payment for consulting services rendered."
  }'
```

**2. Observar el pipeline**

El proceso se ejecuta en background. La respuesta inicial devuelve el `process_id` con estado `pending`. A los pocos segundos el estado cambia a `completed` o `awaiting_approval`.

**3. Revisar el resultado**

En la página **Processes**, buscar el proceso por ID o título. El detalle muestra:
- Tipo clasificado y confidence score
- Campos extraídos
- Decisión tomada y razonamiento
- Acción ejecutada o en espera

**4. Aprobar o rechazar (si aplica)**

Si el proceso quedó en `awaiting_approval`, ir a la sección **Approvals**, ingresar nombre del revisor y notas opcionales, y confirmar la decisión.

**5. Consultar métricas**

La sección **Metrics** muestra volumen diario, distribución por tipo y estado, y distribución de confidence scores.

---

## Notas importantes

- **Datos de demostración** — el script `seed_data.py` genera 10 procesos realistas con distintos tipos, montos y estados. Útil para explorar el sistema sin enviar inputs manuales.
- **Ejecución de acciones simulada** — todas las acciones (send_email, create_record, approve_payment, etc.) son simuladas. No se realizan operaciones reales sobre sistemas externos.
- **LLM opcional** — si no se configura `LLM_API_KEY`, el sistema opera en modo rule-based usando regex y pattern matching. La funcionalidad completa está disponible sin API key.
- **Umbrales configurables** — los parámetros `CONFIDENCE_AUTO_THRESHOLD`, `CONFIDENCE_REVIEW_THRESHOLD` y `HIGH_VALUE_THRESHOLD` se ajustan en el archivo `.env`.
- **Base de datos** — en desarrollo usa SQLite (`backend/data/agent.db`). Para producción, cambiar `DATABASE_URL` a una conexión PostgreSQL y ejecutar migraciones con Alembic.

---

## API Reference

Endpoints principales:

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/v1/ingestion/submit` | Enviar input para procesamiento |
| `GET` | `/api/v1/processes` | Listar procesos (filtros, búsqueda, paginación) |
| `GET` | `/api/v1/processes/{id}` | Detalle con decisiones, acciones y audit trail |
| `DELETE` | `/api/v1/processes/{id}` | Eliminar proceso |
| `GET` | `/api/v1/approvals` | Listar aprobaciones por estado |
| `POST` | `/api/v1/approvals/{id}/approve` | Aprobar acción pendiente |
| `POST` | `/api/v1/approvals/{id}/reject` | Rechazar acción pendiente |
| `GET` | `/api/v1/metrics/summary` | Resumen de KPIs |
| `GET` | `/api/v1/metrics/volume?days=7` | Serie temporal de volumen |
| `GET` | `/api/v1/metrics/breakdown` | Distribución por tipo, estado y confidence |
| `GET` | `/api/v1/audit/logs` | Log de auditoría paginado |

---

## Licencia

MIT
