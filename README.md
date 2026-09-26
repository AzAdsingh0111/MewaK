# 🛍️ MewaK - Full-Stack E-Commerce & Analytics Platform

A modern, containerized E-Commerce marketplace platform featuring **FastAPI Backend**, **Streamlit Interactive Frontend**, **PostgreSQL Relational Storage**, **Real-Time Slack Webhook Alerts**, and **Automated Daily Executive Reports (PDF & Excel)**.

---

## 🏗️ Architecture Overview

| Component | Technology | Description | Default Port |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | Streamlit | Storefront, Cart, Checkout, Admin Ingestion Portal | `8501` |
| **Backend REST API** | FastAPI + Pydantic | Authentication, Catalog Management, Inventory, Checkout | `8000` |
| **Database** | PostgreSQL 16 | Relational tables with constraints, enums, indexes | `5432` |
| **Notification Engine** | Slack Webhook API | Instant alerts for orders, low-stock & order fulfillment | External |
| **Executive Reports** | Python + FPDF + OpenPyXL | Automated daily sales reports in PDF & Multi-sheet Excel | Background |

---

## 🚀 Quick Start with Docker Compose

Run all services together with a single command:

```bash
docker-compose up --build
```

### Accessing the Platform:
- **Streamlit Web Application**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Interactive Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI Alternative Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 💻 Local Development (Without Docker)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start FastAPI Backend
```bash
uvicorn mewak_api:app --reload --port 8000
```

### 3. Start Streamlit Frontend
```bash
streamlit run mewak_ecommerce_app_v2.py
```

### 4. Run Daily Report Worker Manually
```bash
python daily_report_worker.py
```

---

## 🔑 Default Accounts

| Email | Password | Role | Access Level |
| :--- | :--- | :--- | :--- |
| `admin@mewak.com` | `admin123` | **ADMIN** | Storefront, Owner Portal, Bulk CSV Ingestion |
| `buyer@example.com` | `user123` | **CUSTOMER** | Storefront, Cart, Checkout, Order Tracking |

---

## 🔔 Slack Webhook Setup

To enable live Slack alerts:
1. Create an Incoming Webhook in your Slack Workspace.
2. Add your webhook URL to `.env` or pass as environment variable:
   ```env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```
3. Whenever a customer places an order or stock falls below 10 units, formatted block alerts are dispatched automatically.
