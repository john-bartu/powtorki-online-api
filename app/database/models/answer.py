from sqlalchemy import Column, Integer, VARCHAR, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class MapPageAnswer(Base):
    __tablename__ = "map_question_answer"

    id = Column(Integer, primary_key=True, index=True)
    id_question = Column(Integer, ForeignKey("pages.id"))
    id_answer = Column(Integer, ForeignKey("answers.id"))
    is_correct = Column(Integer)
    answer = relationship("Answer", lazy='joined')


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    answer = Column(VARCHAR(100))
