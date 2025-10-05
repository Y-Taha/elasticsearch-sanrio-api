from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from uuid import uuid4
import time

from elastic_client import get_es_client
from schemas import CharacterCreate
from models import ensure_index, CHAR_INDEX
from logging_config import setup_logging

app = FastAPI(title='Sanrio Characters API')
logger = setup_logging()

es = get_es_client()
ensure_index(es)


# -------------------------------
# ✅ Middleware: log every request/response
# -------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid4())
    start_time = time.time()
    try:
        response = await call_next(request)
        duration = round(time.time() - start_time, 4)
        logger.info({
            "request_id": request_id,
            "event": "request_completed",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_seconds": duration,
            "client": request.client.host if request.client else None
        })
        return response
    except Exception as e:
        duration = round(time.time() - start_time, 4)
        logger.error({
            "request_id": request_id,
            "event": "request_failed",
            "method": request.method,
            "path": request.url.path,
            "error": str(e),
            "duration_seconds": duration
        })
        raise


# -------------------------------
# ✅ Error model and handler
# -------------------------------
class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    logger.error({
        "request_id": str(uuid4()),
        "event": "api_error",
        "path": request.url.path,
        "status_code": exc.status_code,
        "error_code": exc.code,
        "message": exc.message
    })
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message}
    )


# -------------------------------
# ✅ CRUD endpoints with logging
# -------------------------------
@app.post("/characters")
async def create_character(payload: CharacterCreate, request: Request):
    doc = payload.dict()
    res = es.index(index=CHAR_INDEX, document=doc)
    doc_id = res["_id"]

    logger.info({
        "request_id": str(uuid4()),
        "event": "character_created",
        "path": request.url.path,
        "status_code": 201,
        "elasticsearch_doc_id": doc_id,
        "payload": doc
    })

    return {"id": doc_id, **doc}


@app.get("/characters/{char_id}")
async def get_character(char_id: str, request: Request):
    try:
        res = es.get(index=CHAR_INDEX, id=char_id)
    except Exception:
        raise APIError("NOT_FOUND", f"Character {char_id} not found", status_code=404)

    logger.info({
        "request_id": str(uuid4()),
        "event": "character_fetched",
        "path": request.url.path,
        "status_code": 200,
        "elasticsearch_doc_id": char_id
    })

    return {"id": res["_id"], **res["_source"]}


@app.put("/characters/{char_id}")
async def update_character(char_id: str, payload: CharacterCreate, request: Request):
    try:
        es.get(index=CHAR_INDEX, id=char_id)
    except Exception:
        raise APIError("NOT_FOUND", f"Character {char_id} not found", status_code=404)
    es.index(index=CHAR_INDEX, id=char_id, document=payload.dict())

    logger.info({
        "request_id": str(uuid4()),
        "event": "character_updated",
        "path": request.url.path,
        "status_code": 200,
        "elasticsearch_doc_id": char_id,
        "payload": payload.dict()
    })

    return {"id": char_id, **payload.dict()}


@app.delete("/characters/{char_id}")
async def delete_character(char_id: str, request: Request):
    try:
        es.delete(index=CHAR_INDEX, id=char_id)
    except Exception:
        raise APIError("NOT_FOUND", f"Character {char_id} not found", status_code=404)

    logger.info({
        "request_id": str(uuid4()),
        "event": "character_deleted",
        "path": request.url.path,
        "status_code": 200,
        "elasticsearch_doc_id": char_id
    })

    return {"result": "deleted", "id": char_id}


@app.get("/search")
async def search(
    q: str = None,
    franchise: str = None,
    species: str = None,
    tags: str = None,
    page: int = 1,
    size: int = 10,
    fuzzy: bool = False
):
    must = []

    if q:
        must.append({
            "multi_match": {
                "query": q,
                "fields": ["name^3", "description"],
                **({"fuzziness": "AUTO"} if fuzzy else {})
            }
        })

    if franchise:
        must.append({"term": {"franchise": franchise}})
    if species:
        must.append({"term": {"species": species}})
    if tags:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        must.append({"terms": {"tags": tags_list}})

    body = {
        "from": (page - 1) * size,
        "size": size,
        "query": {"bool": {"must": must}} if must else {"match_all": {}}
    }

    res = es.search(index=CHAR_INDEX, body=body)
    hits = [{"id": h["_id"], **h["_source"]} for h in res["hits"]["hits"]]

    logger.info({
        "request_id": str(uuid4()),
        "event": "search_executed",
        "query": q,
        "filters": {"franchise": franchise, "species": species, "tags": tags},
        "page": page,
        "size": size,
        "results_count": len(hits)
    })

    return {
        "total": res["hits"]["total"]["value"],
        "page": page,
        "size": size,
        "hits": hits
    }
