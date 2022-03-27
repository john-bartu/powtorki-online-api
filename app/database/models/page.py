import json

from sqlalchemy import Column, Integer, String, VARCHAR, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.render.templater import render_template


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    id_author = Column(Integer, ForeignKey("users.id"))
    id_type = Column(Integer, ForeignKey("page_types.id"))
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
        'polymorphic_identity': 2
    }


class ScriptPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': 3
    }


class CharacterPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': 4
    }

    def format(self):
        return render_template('character-box.html', NAME=self.title, DESCRIPTION=self.description)


class CalendarPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': 5
    }

    date = relationship("Date", back_populates="page", uselist=False)

    def format(self):
        return render_template('calendar-box.html', NAME=self.title, DESCRIPTION=self.description)


class DictionaryPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': 6
    }

    def format(self):
        return render_template('dictionary-box.html', NAME=self.title, DESCRIPTION=self.description)


class QAPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': 7
    }


class QuizPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': 8
    }

    map_answers = relationship("MapPageAnswer", uselist=True)
    answers = relationship("PageAnswer", uselist=True)


class MindmapPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': 9
    }
