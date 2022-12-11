import json

from sqlalchemy import Column, Integer, String, VARCHAR, ForeignKey, DateTime, func, Float
from sqlalchemy.orm import relationship

from app.constants import PageTypes
from app.database.database import Base
from app.render.templater import render_template


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    id_author = Column(Integer, ForeignKey("users.id"))
    id_type = Column(Integer, ForeignKey("page_types.id"))
    id_sub_type = Column(Integer, ForeignKey("page_sub_types.id"))
    order_no = Column(Integer)
    title = Column(VARCHAR(255))
    document = Column(String)
    description = Column(VARCHAR(255))
    note = Column(VARCHAR(255))

    time_creation = Column(DateTime(timezone=True), server_default=func.now())
    time_edited = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    taxonomies = relationship("MapPageTaxonomy", uselist=True, back_populates="page")

    __mapper_args__ = {
        'polymorphic_on': id_type,
        'polymorphic_identity': 1
    }

    def __repr__(self):
        filter_names = ['id', 'id_author', 'id_type', 'title', 'document', 'description', 'note']
        return json.dumps({index: str(value) if index in filter_names else "" for index, value in vars(self).items()})


class DocumentPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.DocumentPage
    }

    media = relationship("PageMedia", uselist=True)


class CharacterPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.CharacterPage
    }

    def format(self):
        return render_template('character-box.html', NAME=self.title, DESCRIPTION=self.document)


class CalendarPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.CalendarPage
    }

    date = relationship("Date", back_populates="page", uselist=False)

    def format(self):
        return render_template('calendar-box.html', NAME=self.title, DESCRIPTION=self.document)


class DictionaryPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.DictionaryPage
    }

    def format(self):
        return render_template('dictionary-box.html', NAME=self.title, DESCRIPTION=self.document)


class QAPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.QAPage
    }


class QuizPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.QuizPage
    }

    map_answers = relationship("MapPageAnswer", uselist=True, back_populates='page')
    answers = relationship("PageAnswer", uselist=True)


class UserQuizAnswer(Base):
    __tablename__ = "map_user_quiz_answer"

    id = Column(Integer, primary_key=True, index=True)
    id_answer = Column(Integer, ForeignKey("answers.id"))
    id_user = Column(Integer, ForeignKey("users.id"))
    date_answer = Column(DateTime(timezone=True), server_default=func.now())


class UserActivity(Base):
    __tablename__ = "map_user_activity"

    id = Column(Integer, primary_key=True, index=True)
    id_page = Column(Integer, ForeignKey("pages.id"))
    id_user = Column(Integer, ForeignKey("users.id"))
    knowledge = Column(Float)
    time_creation = Column(DateTime(timezone=True), server_default=func.now())
    page = relationship("Page", uselist=False)
