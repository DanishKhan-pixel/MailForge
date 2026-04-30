# Email Automation System (FastAPI)

Production-style FastAPI project to upload a CSV file and send personalized emails one-by-one through Gmail SMTP with safe throttling, retries, status tracking, and logs.

## Features

- FastAPI backend with modular clean structure (`routes`, `services`, `utils`, `models`)
- CSV upload + parsing (`email` required, `name` optional)
- Email validation before sending
- Personalized templates with placeholders (example: `Hello {name}`)
- Background email sending using FastAPI `BackgroundTasks`
- Sequential sending with configurable 3-5 second delay
- Retry support for transient failures
- Status endpoint for progress tracking
- File logging for sent/failed emails
- Environment variable based SMTP credential management
- Basic in-memory rate limiting for key endpoints

## Project Structure

```text
app/
  main.py
  routes/
    csv_routes.py
    email_routes.py
    status_routes.py
  services/
    csv_service.py
    email_service.py
    state_service.py
  utils/
    config.py
    email_validator.py
    logger.py
    rate_limit.py
    template.py
  models/
    schemas.py
requirements.txt
.env.example
sample_data/recipients.csv
```

## Prerequisites

- Python 3.11+ recommended
- Gmail account with **App Password** enabled
  - Do not use your normal Gmail password

## Setup

1. Create virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create your env file:

```bash
cp .env.example .env
```

3. Edit `.env` with your real Gmail credentials:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_gmail_address@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM_EMAIL=your_gmail_address@gmail.com
RETRY_COUNT=2
```

4. Run the API:

```bash
uvicorn app.main:app --reload
```

5. Open Swagger docs:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## API Endpoints

- `POST /api/upload-csv`
  - Form-data: `file` (CSV)
  - Required CSV column: `email`
  - Optional CSV column: `name`

- `POST /api/send-emails`
  - JSON body example:
  ```json
  {
    "subject": "Welcome to our service",
    "message": "Hello {name}, thanks for joining us!",
    "delay_seconds": 4
  }
  ```

- `GET /api/status`
  - Returns running state, totals, success count, failure count, and latest error

- `GET /health`
  - Basic health check

## Safe Sending Notes

- Emails are sent one by one (not batched in single SMTP call)
- Delay is enforced between sends to reduce spam-like behavior
- Failures are logged and the system continues with remaining recipients
- Retries are attempted before marking a recipient as failed

## Logs

- Runtime logs are written to:
  - `logs/email_automation.log`

## Example CSV

See:

- `sample_data/recipients.csv`

## Important Security Note

- Never commit `.env` to git
- Keep your SMTP app password private
