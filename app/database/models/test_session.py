from sqlalchemy import Column, Integer, VARCHAR, ForeignKey, DateTime, Boolean, JSON, UniqueConstraint, Index, func
from sqlalchemy.orm import relationship

from app.database.database import Base


class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id"), nullable=False)
    id_taxonomy = Column(Integer, ForeignKey("taxonomies.id"), nullable=False)
    included_types = Column(JSON, nullable=False)
    status = Column(VARCHAR(20), nullable=False, default="in_progress")
    time_creation = Column(DateTime(timezone=True), server_default=func.now())
    time_completed = Column(DateTime(timezone=True), nullable=True)

    pages = relationship("TestSessionPage", uselist=True, back_populates="session")


class TestSessionPage(Base):
    __tablename__ = "map_test_session_page"

    id = Column(Integer, primary_key=True, index=True)
    id_test_session = Column(Integer, ForeignKey("test_sessions.id"), nullable=False)
    id_page = Column(Integer, ForeignKey("pages.id"), nullable=False)
    is_known = Column(Boolean, nullable=False)
    # Which answer was actually submitted -- quiz grades only (flashcard grading has no
    # answer choice, just a self-reported known/unknown), kept for session review/history.
    id_answer = Column(Integer, ForeignKey("answers.id"), nullable=True)
    time_answered = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("TestSession", uselist=False, back_populates="pages")
    page = relationship("Page", uselist=False)
    answer = relationship("Answer", uselist=False)

    __table_args__ = (
        UniqueConstraint("id_test_session", "id_page", name="uq_test_session_page"),
        Index("ix_map_test_session_page_id_page", "id_page"),
    )
