# Email Automation System (Production-Ready FastAPI)

Scalable campaign-based email automation backend using FastAPI, PostgreSQL, SQLAlchemy, Alembic, Celery, and Redis.

## Features

- Campaign lifecycle management (`pending`, `running`, `completed`)
- Recipient upload through CSV (`email` required, `name` optional)
- Personalized email templates with placeholders like `{name}`
- Async sending with Celery worker (non-blocking API)
- Retry support and per-recipient status tracking
- Email logs persisted in PostgreSQL and app logs stored in file
- Recipient listing per campaign and privacy-masked email logging
- Pagination and campaign status filtering
- Basic API rate limiting and environment-driven configuration
- SMTP delivery with bounded retries and per-recipient privacy-masked logging
- Recipient listing with pagination and validated campaign status filters
- CSV sanitization including email size limits and name length truncation
- Campaign aggregate statistics endpoint exposing global delivery totals
- Email subject sanitization preventing SMTP header injection
- Pydantic email validation for recipient and payload schemas
- Bounded-memory rate limiting with stale bucket eviction
- Configurable SMTP timeout and application log directory
- Case-insensitive unique recipient constraint enforced at database level
- Chunked recipient bulk insertion for memory-efficient large uploads

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

## Running Tests

Execute the automated pytest suite for unit, service, and API integration testing:

```bash
pytest
```

The test suite covers:
- **API Endpoints**: Health checks and web dashboard endpoints.
- **CSV Service**: Recipient CSV validation, formatting, and deduplication logic.
- **Campaign Service**: Telemetry calculations and sending preconditions.
- **Rate Limiting**: Sliding window request throttling and cache resets.
- **Configuration & Logging**: Environment settings resolution and log handler setup.
- **ORM Models**: Representation methods and status enumeration integrity.
- **Workers & Email Services**: Template rendering and SMTP delivery logic.
- **Modular Package Exports**: Clean top-level package exports across `core`, `db`, `services`, `workers`, and `api`.
- **Accessibility & Templates**: ARIA progress bar tags and HTML template rendering.
- **Formatting Utilities**: Privacy-preserving email masking (`mask_email`) and ISO 8601 UTC timestamp formatting.
- **Schema Validation**: Granular Pydantic models (`RecipientItem`, `SendOptions`, `PaginationParams`).
- **SMTP Retry**: Bounded retry on transient email failures with exponential backoff.
- **Celery Configuration**: Broker, serialization, and timezone configuration verified.
- **Rate Limiting**: Per-configuration bucket isolation preventing cross-endpoint contention.
- **Worker Execution Status**: Task status constants (`TASK_STATUS_COMPLETED`, `TASK_STATUS_MISSING_CAMPAIGN`).
- **Recipient APIs**: Campaign recipient listing endpoint with paginated response and 404 guarding.
- **Worker Log Privacy**: Emails masked in worker logs via `mask_email`.
- **CSV Deduplication**: Case-insensitive recipient deduplication keeping first occurrence.
- **Batch Processing Utilities**: List partitioning (`chunk_list`) for memory-efficient bulk processing.
- **Query Filter Schemas**: Validated query parameter filters (`CampaignQueryFilter`) for campaign listing.
- **OpenAPI Metadata**: Categorized tags metadata (`Campaigns`, `Health`, `UI`) for Swagger UI documentation.
- **Email Payload Schemas**: Validated payload schemas (`EmailPayload`) for individual email sending requests.
- **Domain Utilities**: Email domain extraction (`extract_email_domain`) for routing and analytics.
- **Error Response Schemas**: Standardized error detail schemas (`ErrorDetail`) for consistent API error responses.
- **Header Injection Protection**: Email subject lines sanitized against line-break injection.
- **Email Schema Validation**: `RecipientItem` and `EmailPayload` validated with `EmailStr`.
- **Campaign Stats**: Aggregate totals endpoint exposing campaign, sent, and failed counts.
- **Rate Limiter Bounding**: Sliding-window buckets swept and evicted to cap memory use.
- **Chunked Recipient Upload**: Recipient rows bulk-inserted in bounded chunks.
- **Configurable SMTP & Logging**: SMTP timeout, log directory, and log file name via settings.
- **Database Uniqueness**: Case-insensitive unique index on campaign recipient emails.
- **HTML Sanitization**: HTML tag stripping utility (`strip_html_tags`) for plain text email conversion.
- **Campaign Breakdown Schemas**: Detailed status breakdown schema model (`CampaignSummaryStats`) for dashboard telemetry.
- **Service Summary Aggregations**: Helper function (`get_campaign_summary_counts`) computing campaign status tallies.
- **Test Environment Property**: Environment setting flag (`is_testing`) identifying active test executions.
- **API Overview Response Schema**: System runtime overview response schema (`ApiStatusResponse`).
- **Email Normalization**: Lowercase domain and whitespace stripping utility (`normalize_email`).
- **Telemetry System Info Schema**: Environment and infrastructure response model (`SystemInfoResponse`).
- **Local Infra Flag**: Settings property (`is_local`) detecting localhost infrastructure connectivity.
- **Empty Campaign Validation**: Service helper function (`is_empty_campaign`) detecting unpopulated campaigns.
- **Batch Deletion Response Schema**: Standardized response model (`BulkDeleteResponse`) for deletion operations.
- **Byte Size Formatting**: Human-readable file size formatting utility (`format_file_size`).
- **Batch Result Telemetry**: Generic operation status model (`BatchOperationResult`) for bulk processing.
- **SMTP SSL Property**: Settings flag (`is_ssl_enabled`) identifying port 465 SSL connection mode.
- **Campaign State Guard**: Service helper (`is_campaign_editable`) validating campaign modification status.
- **Filter Query Parameters**: Validated query filter model (`FilterParams`) for API endpoints.
- **Email Domain Validation**: Domain syntax validation helper function (`is_valid_email_domain`).
- **Date Range Filters**: Datetime boundary filter schema (`DateRangeFilter`) for query filtering.
- **Sorting Parameters**: Column sorting configuration schema (`SortParams`) with asc/desc direction validation.
- **HTML Content Detection**: Tag detection utility function (`is_html_content`) identifying HTML body markup.
- **Pagination Query Offset**: Computed property (`PaginationParams.offset`) calculating SQL database query offset.
- **Custom SMTP Port Flag**: Settings property (`is_custom_smtp_port`) flagging non-standard SMTP server ports.
- **Campaign Execution Duration**: Service helper (`get_campaign_duration_seconds`) computing elapsed campaign runtime.






