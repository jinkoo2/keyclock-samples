# Keycloak Samples

This folder contains a minimal Keycloak + backend + frontend stack using Docker Compose. It is intended for local development and experimentation.

## What’s included

- **Keycloak** (latest) with its own Postgres DB.
- **Backend**: builds from `../backend`, runs on `http://localhost:8000`.
- **Frontend**: builds from `../frontend`, served on `http://localhost:3000`.
- **Databases**: Postgres for app data and Keycloak data.

## Prerequisites

- Docker and Docker Compose installed.

## Usage

1) From the repo root:

```bash
cd keycloak-samples
docker compose up --build
```

2) Services:
   - Keycloak: http://localhost:8080
   - Backend:  http://localhost:8000
   - Frontend: http://localhost:3000

3) Default credentials (environment overrideable):
   - `KEYCLOAK_ADMIN=admin`
   - `KEYCLOAK_PASSWORD=changeme`
   - App DB: `docuforms` / `docuforms` / `${POSTGRES_PASSWORD:-changeme}`

4) Stopping:

```bash
docker compose down
```

## Notes

- Backend and frontend build context is relative: `../backend` and `../frontend`.
- Volumes: `postgres_data`, `keycloak_db_data` persist database state.
- CORS and Keycloak config in the backend should match your realm/client IDs; defaults are set via environment variables in the compose file.

