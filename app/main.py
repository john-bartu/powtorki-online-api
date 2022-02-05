from fastapi import FastAPI

from app.database.database import SessionLocal
from app.routers import character

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"status": "ok"}


app.include_router(character.router)
