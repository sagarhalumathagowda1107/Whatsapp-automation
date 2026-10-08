# Weekly WhatsApp PDF Report Automation System

A production-ready backend application built with **FastAPI**, **PostgreSQL**, **ReportLab**, and the **Official Meta WhatsApp Business Cloud API**.

The application automatically compiles weekly performance and status records (PSF data) from PostgreSQL into a beautifully formatted PDF report every week, uploads the PDF to Meta's Cloud API, and sends it directly to configured WhatsApp recipients with real-time delivery status tracking via Webhooks (`sent`, `delivered`, `read`, `failed`).

---

## Architecture Overview

```
                          ┌───────────────────────────┐
                          │   APScheduler (Weekly)    │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
┌──────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│   PostgreSQL     │◄────►│   FastAPI Backend System  │─────►│  ReportLab Engine (PDF)   │
│  (PSF & Logs)    │      └─────────────┬─────────────┘      └───────────────────────────┘
└──────────────────┘                    │
                                        ▼
                          ┌───────────────────────────┐
                          │   Meta WhatsApp Cloud API │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │    WhatsApp Recipients    │
                          └───────────────────────────┘
```

### Key Technical Highlights

1. **Clean Modular Layering**: Separates API routers, Pydantic v2 schemas, SQLAlchemy 2.x models, and dedicated service objects.
2. **Official Meta API Compliance**: Uses direct Meta Graph API HTTP endpoints. Strictly **no** browser automation, Selenium, or unofficial APIs.
3. **ReportLab PDF Engine**: Generates multi-page PDF documents featuring company headers, running footers with dynamic page numbers (`Page X of Y`), executive summary boxes, category breakdown tables, and detailed PSF logs.
4. **Idempotency Guard**: APScheduler checks database records before generating weekly reports to prevent duplicate sends when the server or container restarts.
5. **Real-time Webhook Callbacks**: Validates Meta webhook challenges (`GET`) and receives event updates (`POST`) to record `sent`, `delivered`, `read`, and `failed` timestamps.
6. **Mock Testing Mode**: Set `WHATSAPP_MOCK_MODE=true` to test end-to-end report generation and dispatch workflows without real Meta API credentials.

---

## Technology Stack

- **Language**: Python 3.12+
- **API Framework**: FastAPI & Uvicorn
- **Database**: PostgreSQL 16 with SQLAlchemy 2.x ORM & Alembic migrations
- **PDF Engine**: ReportLab 4.x
- **Scheduler**: APScheduler (Cron Trigger with Configurable Timezones)
- **HTTP Client**: `httpx` (Async)
- **Validation**: Pydantic v2 & `pydantic-settings`
- **Testing**: `pytest`, `pytest-asyncio`, `respx`
- **Containerization**: Docker & Docker Compose

---

## Project Structure

```
.
├── alembic.ini                  # Alembic CLI configuration
├── alembic/                      # Database migration scripts
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entry point & lifespan manager
│   ├── config.py                # Environment configuration settings
│   ├── api/                     # REST API routers & dependencies
│   │   ├── deps.py              # API Key authorization dependency
│   │   └── v1/
│   │       ├── health.py        # /api/v1/health status
│   │       ├── psf.py           # /api/v1/psf CRUD & search
│   │       ├── recipients.py    # /api/v1/recipients management
│   │       ├── reports.py       # /api/v1/reports generation & dispatch
│   │       └── whatsapp.py      # /api/v1/whatsapp webhooks & test endpoint
│   ├── db/                      # Database layer
│   │   ├── base.py              # Declarative base model
│   │   ├── session.py           # Engine & SessionLocal setup
│   │   └── models/              # SQLAlchemy models (PSF, Recipient, Report, MessageLog)
│   ├── schemas/                 # Pydantic v2 request/response schemas
│   └── services/                # Business logic services
│       ├── pdf_service.py       # ReportLab PDF template generator
│       ├── psf_service.py       # PSF data access layer
│       ├── recipient_service.py # Recipient management & normalization
│       ├── report_service.py    # Report orchestration & retries
│       ├── scheduler_service.py # APScheduler weekly task & idempotency
│       └── whatsapp_service.py  # Meta WhatsApp Business Cloud API client
├── tests/                       # Pytest automated test suite
├── Dockerfile                   # Docker production image build
├── docker-compose.yml           # PostgreSQL + FastAPI Compose environment
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
└── README.md                    # Documentation
```

---

## Environment Variables & `.env` Setup

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ADMIN_API_KEY` | `admin-secret-key` | Secret key sent in `X-API-Key` header for admin routes |
| `DATABASE_URL` | `postgresql+psycopg://...` | PostgreSQL connection URI |
| `WHATSAPP_ACCESS_TOKEN` | `your_token` | Meta WhatsApp Cloud API Permanent/System User Token |
| `WHATSAPP_PHONE_NUMBER_ID` | `your_id` | Meta Phone Number ID |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | `your_waba_id` | Meta WhatsApp Business Account ID |
| `WHATSAPP_VERIFY_TOKEN` | `your_webhook_token` | Secret string for Meta Webhook verification |
| `WHATSAPP_API_VERSION` | `v20.0` | Meta Graph API Version |
| `WHATSAPP_MOCK_MODE` | `false` | Set `true` for mock testing without real WhatsApp credentials |
| `REPORT_DAY` | `MONDAY` | Day of week for weekly report delivery (`MONDAY`, `TUESDAY`, etc.) |
| `REPORT_TIME` | `09:00` | Time of day (`HH:MM` 24-hr format) |
| `REPORT_TIMEZONE` | `Asia/Kolkata` | Schedule timezone |
| `REPORT_STORAGE_PATH` | `reports/generated` | Local directory path to store generated PDFs |

---

## Meta WhatsApp Business Setup Guide

To use real WhatsApp delivery:

1. **Meta Developer Portal**: Go to [developers.facebook.com](https://developers.facebook.com) and create an App of type **Business**.
2. **Add WhatsApp Product**: Select **WhatsApp** from the products list.
3. **Get Phone Number ID**: Under **WhatsApp > API Setup**, copy the **Phone Number ID**.
4. **Temporary vs System User Access Token**:
   - For temporary testing, use the 24-hour token from API Setup.
   - For production, create a **System User** in Meta Business Manager, assign the WhatsApp Business App, grant `whatsapp_business_messaging` and `whatsapp_business_management` permissions, and generate a **Permanent Access Token**.
5. **Configure Webhook**:
   - Set Callback URL: `https://your-domain.com/api/v1/whatsapp/webhook`
   - Set Verify Token: Match `WHATSAPP_VERIFY_TOKEN` in `.env`.
   - Subscribe to field: `messages`.

> [!NOTE]
> Outbound business-initiated messages to WhatsApp users may require recipient consent and approved Meta Message Templates depending on Meta policies for your region.

---

## Running Locally

### 1. Install Dependencies & Setup DB
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Apply Alembic Migrations
```bash
alembic upgrade head
```

### 3. Run FastAPI Application
```bash
uvicorn app.main:app --reload --port 8000
```

Access Swagger UI documentation at: `http://localhost:8000/docs`

---

## Running with Docker & Docker Compose

Start FastAPI and PostgreSQL containers:

```bash
docker compose up --build
```

The system will automatically apply database migrations on boot and start serving at `http://localhost:8000`.

---

## Automated Pytest Suite

Run all unit and integration tests (using SQLite in-memory database and mocked Meta API):

```bash
pytest -v
```

---

## Example `curl` Commands

### 1. Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

### 2. Add PSF Performance Record
```bash
curl -X POST "http://localhost:8000/api/v1/psf" \
  -H "X-API-Key: admin-secret-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Database Optimization Complete",
    "description": "Indexed primary tables and tuned connection pool",
    "category": "Infrastructure",
    "value": {"queries_per_sec": 4500},
    "status": "COMPLETED"
  }'
```

### 3. Add Recipient
```bash
curl -X POST "http://localhost:8000/api/v1/recipients" \
  -H "X-API-Key: admin-secret-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "phone_number": "+14155552671",
    "active": true
  }'
```

### 4. Manually Generate & Send Weekly Report Immediately
```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "X-API-Key: admin-secret-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "send_immediately": true
  }'
```

### 5. Send Test Text Message to WhatsApp Number
```bash
curl -X POST "http://localhost:8000/api/v1/whatsapp/test-send?to_phone=%2B14155552671&message=Hello%20world" \
  -H "X-API-Key: admin-secret-key-change-me"
```

### 6. Retry Failed WhatsApp Report Deliveries
```bash
curl -X POST "http://localhost:8000/api/v1/reports/<REPORT_ID>/retry" \
  -H "X-API-Key: admin-secret-key-change-me"
```

---

## Deployment Guide (Railway & Render)

> [!WARNING]
> **Vercel is NOT recommended** for this system because Vercel serverless functions have execution timeouts and do not support long-running background APScheduler tasks or persistent local storage for generated PDFs.

### Deploying to Railway
1. Push your repository to GitHub.
2. Create a new project on [Railway.app](https://railway.app).
3. Provision a **PostgreSQL Database** plugin.
4. Create a **Web Service** connected to your GitHub repo (select Dockerfile).
5. Set Environment Variables in Railway matching `.env.example` (set `DATABASE_URL` to Railway's Postgres URL).

### Deploying to Render
1. Create a **PostgreSQL Database** on Render.
2. Create a **Web Service** on Render selecting **Docker runtime**.
3. Attach environment variables.
4. Optional: If your platform restarts web instances frequently, create a separate Worker process on Render running `python -m app.services.scheduler_service` to isolate the scheduler.
