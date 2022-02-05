from fastapi import FastAPI
from app.routers import character

app = FastAPI()


@app.get("/")
def read_root():
    return {"status": "ok"}


app.include_router(character.router)
