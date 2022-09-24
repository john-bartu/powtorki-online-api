import time
from urllib.request import Request

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.routers import knowledge, auth, quiz

app = FastAPI()

origins = ["https://platforma.powtorkionline.pl"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def current_time_millis():
    return time.time() * 1000


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = current_time_millis()
    response = await call_next(request)
    process_time = current_time_millis() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
def read_root():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(quiz.router)
app.include_router(knowledge.router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Powtórki Online API",
        version="0.5.0",
        description="Powtórki Online OpenAPI schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
