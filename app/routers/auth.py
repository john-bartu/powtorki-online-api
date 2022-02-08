from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, Response

from app.session.cookie import cookie
from app.session.session import app_session
from app.session.session_date import SessionData, SessionPost
from app.session.verifier import verifier

router = APIRouter(
    prefix="/session",
    tags=["session"],
)


@router.post("/")
async def create_session(form: SessionPost, response: Response):
    session = uuid4()
    data = SessionData(username=form.username)
    print("password:" + form.password)

    await app_session.create(session, data)
    cookie.attach_to_response(response, session)

    return data


@router.get("/", dependencies=[Depends(cookie)])
async def check_session(session_data: SessionData = Depends(verifier)):
    return session_data


@router.delete("/")
async def remove_session(response: Response, session_id: UUID = Depends(cookie)):
    await app_session.delete(session_id)
    cookie.delete_from_response(response)
    return "deleted session"
