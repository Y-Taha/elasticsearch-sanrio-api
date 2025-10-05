# Elasticsearch Sanrio API

A production-style REST API for managing Sanrio character data, backed by Elasticsearch.

## Features
- CRUD operations for Sanrio characters
- Schema validation (Pydantic)
- Advanced search: filtering, pagination, fuzzy search
- Structured logging (JSON) suitable for Grafana & Power BI ingestion
- Postman collection included
- Unit tests using pytest
- Docker Compose for Elasticsearch + API
- Port-check script for debugging connectivity

## Quick start (development)

Requirements: Docker (optional), Python 3.10+, pip

1. Start Elasticsearch with Docker Compose (optional):

```bash
docker-compose up -d
```

2. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
```

3. Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

4. Open docs: http://localhost:8000/docs

## Endpoints
- `POST /characters` - create a character
- `GET /characters/{id}` - get by id
- `PUT /characters/{id}` - update
- `DELETE /characters/{id}` - delete
- `GET /search` - advanced search with filters, pagination, fuzzy

See Postman collection `postman/sanrio_postman_collection.json` for example calls.

## Logging & Observability
- Logs are written in JSON format to `logs/app.log`.
- Metadata fields: `timestamp`, `level`, `service`, `request_id`, `path`, `status_code`, `error_code`, `message`, `elasticsearch_doc_id`, `payload`
- Grafana: ingest logs via Loki or host the JSON logs in a file source, build dashboards on `status_code` and `error_code` counts.
- Power BI: import JSON logs or create a scheduled export (CSV) from logs and import into Power BI for visualization.

## Testing

```bash
PYTHONPATH=/app pytest -v
```

## Port check script
`python scripts/port_check.py --host <ES_HOST> --port <ES_PORT>`

## Deployment
- Containerize using Dockerfile (example provided inside docs) and deploy behind a reverse proxy.
