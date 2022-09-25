import pytest

import app.database.database
from app.constants import PageTypes
from app.database import models


class Database:
    page_types = {}

    def __init__(self):
        self.connection = app.database.database.SessionLocal()

    def fetch(self):
        for page_type in self.connection.query(models.PageType).all():
            self.page_types[page_type.id] = page_type


constants = {
    "Page": PageTypes.Page,
    "Document": PageTypes.DocumentPage,
    "Script": PageTypes.ScriptPage,
    "Character": PageTypes.CharacterPage,
    "Date": PageTypes.CalendarPage,
    "Dictionary": PageTypes.DictionaryPage,
    "QuestionAnswer": PageTypes.QAPage,
    "Quiz": PageTypes.QuizPage,
    "MindMap": PageTypes.MindmapPage,
    "Video Script": PageTypes.VideoScriptPage
}


@pytest.fixture
def database():
    db = Database()
    db.fetch()
    yield db


@pytest.mark.parametrize("name,expected_id", [(key, value) for key, value in constants.items()])
def test_page_types_constants(database, name, expected_id):
    assert database.page_types[expected_id].name == name
