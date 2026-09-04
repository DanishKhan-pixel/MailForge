# Email Automation System (Production-Ready FastAPI)

Scalable campaign-based email automation backend using FastAPI, PostgreSQL, SQLAlchemy, Alembic, Celery, and Redis.

## Features

- Campaign lifecycle management (`pending`, `running`, `completed`)
- Recipient upload through CSV (`email` required, `name` optional)
- Personalized email templates with placeholders like `{name}`
- Async sending with Celery worker (non-blocking API)
- Retry support and per-recipient status tracking
- Email logs persisted in PostgreSQL and app logs stored in file
- Pagination and campaign status filtering
- Basic API rate limiting and environment-driven configuration

## Architecture

```
app/
main.py
api/
v1/campaigns.py
core/
config.py
logging.py
rate_limit.py
db/
base.py
session.py
models/
campaign.py
recipient.py
email_log.py
schemas/
campaign.py
recipient.py
common.py
services/
campaign_service.py
csv_service.py
email_service.py
workers/
celery_app.py
tasks.py
alembic/
docker-compose.yml
requirements.txt
```

## Setup

### 1) Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
````

### 2) Start Postgres and Redis

```bash
docker compose up -d
```

### 3) Configure environment

```bash
cp .env.example .env
```

Fill real SMTP values in `.env` (use Gmail App Password).

### 4) Run database migrations

```bash
alembic upgrade head
```

### 5) Start API

```bash
uvicorn app.main:app --reload
```

### 6) Start Celery worker

```bash
celery -A app.workers.celery_app.celery_app worker -l info
```
