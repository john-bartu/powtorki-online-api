from uuid import UUID

from fastapi_sessions.backends.implementations import InMemoryBackend

from app.session.session_date import SessionData

app_session = InMemoryBackend[UUID, SessionData]()
