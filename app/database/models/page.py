import json

from sqlalchemy import Column, Integer, String, VARCHAR, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.constants import PageTypes
from app.database.database import Base
from app.render.templater import render_template


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    id_author = Column(Integer, ForeignKey("users.id"))
    id_type = Column(Integer, ForeignKey("page_types.id"))
    order_no = Column(Integer)
    title = Column(VARCHAR(255))
    document = Column(String)
    description = Column(VARCHAR(255))
    note = Column(VARCHAR(255))

    time_creation = Column(String)
    time_edited = Column(String)

    taxonomies = relationship("MapPageTaxonomy", uselist=True)

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


class ScriptPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.ScriptPage
    }


class VideoScriptPage(ScriptPage):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.VideoScriptPage
    }

    media = relationship("PageMedia", uselist=True)


class CharacterPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.CharacterPage
    }

    def format(self):
        return render_template('character-box.html', NAME=self.title, DESCRIPTION=self.description)


class CalendarPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.CalendarPage
    }

    date = relationship("Date", back_populates="page", uselist=False)

    def format(self):
        return render_template('calendar-box.html', NAME=self.title, DESCRIPTION=self.description)


class DictionaryPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.DictionaryPage
    }

    def format(self):
        return render_template('dictionary-box.html', NAME=self.title, DESCRIPTION=self.description)


class QAPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.QAPage
    }


class QuizPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.QuizPage
    }

    map_answers = relationship("MapPageAnswer", uselist=True)
    answers = relationship("PageAnswer", uselist=True)


class MindmapPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': PageTypes.MindmapPage
    }


class UserQuizAnswer(Base):
    __tablename__ = "map_user_quiz_answer"

    id = Column(Integer, primary_key=True, index=True)
    id_answer = Column(Integer, ForeignKey("answers.id"))
    id_user = Column(Integer, ForeignKey("users.id"))
    date_answer = Column(DateTime(timezone=True), server_default=func.now())
