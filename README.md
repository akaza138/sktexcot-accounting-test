# SK Texcot Accounting Software

Full-stack accounting and inventory management software for Textile Industry (Knitting, Dyeing, etc.).

## Features

- **Company Master**: Manage vendors, customers, and internal units.
- **Sales & Billing**: Create GST invoices and purchase bills with auto-ledger posting.
- **Inventory & Process**: Track fabric processing types (Knitting, Dyeing, Pricing).
- **Financials**: 
    - Full Ledger with running balance.
    - Receipts & Payments.
    - Cash & Bank book management.
- **Compliance**:
    - GST Reports (Input/Output).
    - TDS Liability Reports.
- **Tools**:
    - Excel Import (Bulk Data).
    - Dashboard with KPIs and Charts.

## Tech Stack

- **Backend**: Python FastAPI, SQLAlchemy, PostgreSQL.
- **Frontend**: HTML5, CSS3, Vanilla JS (No frameworks).
- **Deployment**: Docker, Docker Compose, Nginx.

## Setup & Running

1. **Prerequisites**: Ensure Docker and Docker Compose are installed.
2. **Configuration**: 
    - Check `.env` handling (Backend already has `.env.example`).
    - Frontend connects to `http://localhost:8000` by default (see `frontend/js/config.js`).

3. **Run Application**:
    ```bash
    docker-compose up --build
    ```

4. **Access**:
    - **Frontend**: http://localhost
    - **API Docs**: http://localhost:8000/docs

## Default Credentials

- **Email**: `admin@sktexcot.com`
- **Password**: `admin123`

## Directory Structure

- `backend/`: FastAPI application code.
- `frontend/`: Static HTML/JS/CSS files.
- `nginx.conf`: Nginx proxy configuration.
- `docker-compose.yml`: Container orchestration.
