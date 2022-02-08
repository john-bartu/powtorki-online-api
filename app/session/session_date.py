from pydantic import BaseModel


class SessionData(BaseModel):
    username: str


class SessionPost(BaseModel):
    username: str
    password: str
