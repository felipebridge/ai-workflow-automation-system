# Architecture Snapshot

_Generated: 2026-05-23_

**74 files** | **2,771 Python LOC**

## Directory Tree

```
ai-workflow-automation-system/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── action_executor.py
│   │   │   ├── classifier.py
│   │   │   ├── decision_engine.py
│   │   │   ├── extractor.py
│   │   │   ├── pipeline.py
│   │   │   └── validator.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── logging_config.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py
│   │   │   └── audit_service.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── scripts/
│   │   ├── __init__.py
│   │   └── seed_data.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_classifier.py
│   │   ├── test_decision_engine.py
│   │   ├── test_extractor.py
│   │   └── test_pipeline.py
│   ├── .env.example
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── approvals.ts
│   │   │   ├── client.ts
│   │   │   ├── metrics.ts
│   │   │   └── processes.ts
│   │   ├── components/
│   │   │   ├── ConfidenceBar.tsx
│   │   │   ├── Layout.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── PriorityBadge.tsx
│   │   │   ├── ProcessTypeIcon.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   └── Timeline.tsx
│   │   ├── pages/
│   │   │   ├── Approvals.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Metrics.tsx
│   │   │   ├── NewProcess.tsx
│   │   │   ├── ProcessDetail.tsx
│   │   │   └── Processes.tsx
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── .gitignore
├── docker-compose.yml
├── README.md
└── start.bat
```

## Module Size (Python LOC)

| Module | LOC |
|--------|-----|
| `backend` | 2,771 |

## Imports

| Module | Uses |
|--------|------|
| `backend` | `anthropic`, `app`, `contextlib`, `datetime`, `fastapi`, `json`, `logging`, `os`, ... (+11) |

## File types

| Extension | Files |
|-----------|------:|
| `.py` | 34 |
| `.tsx` | 16 |
| `.ts` | 6 |
| `.json` | 4 |
| `(none)` | 3 |
| `.js` | 2 |
| `.yml` | 1 |
| `.md` | 1 |
| `.bat` | 1 |
| `.example` | 1 |

---