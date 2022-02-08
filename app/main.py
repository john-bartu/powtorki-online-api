from fastapi import FastAPI

from app.routers import character, date, document

app = FastAPI(

)


@app.get("/")
def read_root():
    return {"status": "ok"}


app.include_router(character.router)
app.include_router(date.router)
app.include_router(document.router)
