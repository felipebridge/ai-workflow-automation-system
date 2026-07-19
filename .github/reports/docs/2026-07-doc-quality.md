# Doc Quality Report

_Date: 2026-07-19_

## README — 100/100 (good)

- Lines: 218

**Sections:**

- AI Workflow Automation System
- Features
- Arquitectura
- Reglas de escalación
- Tech Stack
- Estructura del proyecto
- Cómo ejecutar el proyecto
- Requisitos previos
- Backend
- Frontend
- Accesos
- Docker (alternativa)
- Windows (launcher rápido)
- Flujo de uso
- Notas importantes
- API Reference
- Licencia

## Docstring Coverage

| | |
|--|--|
| Functions | 4/121 (3%) |
| Classes | 0/44 |

**Undocumented public functions (sample):**

- `backend/scripts/seed_data.py::seed`
- `backend/tests/test_decision_engine.py::test_high_confidence_low_risk_is_auto`
- `backend/tests/test_decision_engine.py::test_invoice_under_threshold_is_auto`
- `backend/tests/test_decision_engine.py::test_lead_always_auto_at_high_confidence`
- `backend/tests/test_decision_engine.py::test_payment_request_always_requires_human`
- `backend/tests/test_decision_engine.py::test_high_value_invoice_requires_human`
- `backend/tests/test_decision_engine.py::test_exact_threshold_does_not_trigger`
- `backend/tests/test_decision_engine.py::test_low_confidence_requires_human`
- `backend/tests/test_decision_engine.py::test_medium_confidence_requires_human`
- `backend/tests/test_decision_engine.py::test_multiple_validation_errors_require_human`

## Changelog

No CHANGELOG file.

---