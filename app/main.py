import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import knowledge, auth, quiz, sitemap, test_session

# Configure logging
logging.basicConfig(
    filename="powtorki-api.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler())

app = FastAPI(title="Powtórki Online API")

# Configure CORS
origins = os.getenv('ORIGINS', '*')
if origins != '*':
    origins = [origin.strip() for origin in origins.split(',')]
else:
    origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(quiz.router)
app.include_router(knowledge.router)
app.include_router(sitemap.router)
app.include_router(test_session.router)
