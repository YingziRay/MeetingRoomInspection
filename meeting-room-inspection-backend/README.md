# AI Meeting Room Inspection Backend

FastAPI + PostgreSQL + SQLAlchemy 2 + Alembic skeleton for the meeting-room AI inspection system.

## 1. Prerequisites

- Python 3.12+
- Docker / Docker Compose

## 2. Start PostgreSQL

```bash
docker compose up -d postgres
```

## 3. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 4. Environment

```bash
cp .env.example .env
```

The default database URL targets the local Docker PostgreSQL instance.

## 5. Create first migration

```bash
alembic revision --autogenerate -m "init core tables"
alembic upgrade head
```

## 6. Run API

```bash
uvicorn app.main:app --reload
```

Open:

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health: http://localhost:8000/health

## 7. Current endpoints

### Rooms

- `GET /api/v1/rooms`
- `POST /api/v1/rooms`
- `GET /api/v1/rooms/{room_id}`
- `PATCH /api/v1/rooms/{room_id}`

### Inspection tasks

- `POST /api/v1/inspection-tasks/generate`
- `GET /api/v1/inspection-tasks/{task_id}`
- `POST /api/v1/inspection-tasks/{task_id}/start`
- `POST /api/v1/inspection-tasks/{task_id}/submit`

### Results

- `GET /api/v1/inspection-results/by-task/{task_id}`
- `PATCH /api/v1/inspection-results/{result_id}/confirm`

### Photos

- `POST /api/v1/photos/presign`
- `POST /api/v1/photos/complete`

## 8. Architecture boundaries

- `api/`: HTTP contracts only.
- `services/`: application/business orchestration.
- `models/`: SQLAlchemy persistence model.
- `integrations/vision/`: model-provider abstraction.
- `integrations/storage/`: object-storage abstraction.
- `workers/`: scheduler / async jobs.

Do not put model SDK calls directly in FastAPI routes.

## 9. Database schema included

The initial migration includes meeting rooms, inspection indicators, room-indicator mapping, standard photos, photo regions, inspection tasks, inspection photos, inspection results, AI analysis logs, and inspection-period configuration.

## 10. Next implementation steps

1. Add `inspection_photo`, `standard_photo`, `photo_region`, `room_indicator`, and `inspection_period_config`.
2. Add presigned object-storage upload.
3. Add OpenCV photo-quality checks.
4. Implement `VisionModelProvider` and structured JSON validation.
5. Add async AI jobs and retry handling.
6. Add authentication and enterprise identity integration.
7. Add human-confirmation rules and submission validation.
8. Add notification adapters for DingTalk / WeCom / Feishu.
