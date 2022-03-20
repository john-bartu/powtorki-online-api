import time
from urllib.request import Request

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import knowledge, auth

app = FastAPI()

origins = ["*"]

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


# app.include_router(character.router)
# app.include_router(date.router)
# app.include_router(document.router)
app.include_router(knowledge.router)
app.include_router(auth.router)
