# SER40X Group18 FTAC

Food Truck Accessibility/Analysis platform with:

- A FastAPI backend for ingestion, extraction, scraping config, and report APIs.
- A Node/Express frontend service for dashboard UI, PDF upload, OCR processing, and file management.
- MongoDB for data storage.
- Nginx for static frontend hosting.

## Repository Structure

```text
SER40X-Group18-FTAC/
├── Backend/                 # FastAPI app + business logic modules
├── Frontend/                # Node/Express frontend app and static pages
│   ├── server/              # Express server entrypoint
│   ├── public/              # HTML/CSS/JS/assets
│   ├── data/                # Runtime upload + OCR output files
│   └── tessdata/            # OCR language data files (eng/fra)
├── compose.yaml             # Multi-service Docker Compose orchestration
├── Dockerfile               # Backend image build (Python/FastAPI)
└── nginx.conf               # Nginx config for static frontend mount
```

## Services (Docker Compose)

Defined in `compose.yaml`:

- `backend` (`ftac-backend`)
  - Built from root `Dockerfile`
  - Exposes `8000`
  - Depends on MongoDB
- `frontend` (`ftac-frontend`)
  - Uses `node:20`
  - Runs `npm install && npm start` in `Frontend/`
  - Exposes `3000`
- `nginx`
  - Serves mounted `Frontend/` on port `80`
- `mongodb` (`ftac-mongo`)
  - Exposes `27017` (and mapped `27016`)

## Quick Start (Recommended)

From the project root:

```bash
docker compose up --build
```

Then open:

- Frontend Node app: `http://localhost:3000`
- Frontend static via Nginx: `http://localhost`
- Backend API: `http://localhost:8000`

Stop everything:

```bash
docker compose down
```

This also stops the frontend npm process because it runs inside the `frontend` container.

## Frontend (Standalone Local Run)

If you want to run frontend without Docker:

```bash
cd Frontend
npm install
npm start
```

Open `http://localhost:3000`.

## Backend (Standalone Local Run)

Backend requirements are Python-based and defined in `requirements.txt`.
You can run backend locally with your preferred Python environment, or use Docker Compose for consistency.

## Common Commands

- Rebuild and start all services:
  - `docker compose up --build`
- Start in background:
  - `docker compose up --build -d`
- Stop and remove containers:
  - `docker compose down`
- View logs:
  - `docker compose logs -f`
- View one service logs:
  - `docker compose logs -f frontend`

## Notes

- Runtime frontend file outputs are under `Frontend/data/`:
  - `uploads/`
  - `ocr_processed/`
- OCR language files are under `Frontend/tessdata/`.
- Backend persistence uses MongoDB volumes (`mongodata`, `mongoconfig`).
