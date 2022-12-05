import json

from sqlalchemy import Column, Integer, VARCHAR, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class MapPageAnswer(Base):
    __tablename__ = "map_question_answer"

    id = Column(Integer, primary_key=True, index=True)
    id_question = Column(Integer, ForeignKey("pages.id"))
    id_answer = Column(Integer, ForeignKey("answers.id"))
    is_correct = Column(Integer)

    page = relationship("QuizPage", uselist=False, back_populates="map_answers")
    answer = relationship("Answer", uselist=False)


class PageAnswer(Base):
    __tablename__ = "v_page_quiz_answers"

    id = Column(Integer, primary_key=True, index=True)
    id_question = Column(Integer, ForeignKey("pages.id"))
    id_answer = Column(Integer, ForeignKey("answers.id"))
    is_correct = Column(Integer)
    answer = Column(VARCHAR(255))

    def __repr__(self):
        filter_names = ['id', 'id_question', 'id_answer', 'is_correct', 'answer']
        return json.dumps({index: str(value) if index in filter_names else "" for index, value in vars(self).items()})


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    answer = Column(VARCHAR(255))
