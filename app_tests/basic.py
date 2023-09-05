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
    "Character": PageTypes.CharacterPage,
    "Date": PageTypes.CalendarPage,
    "Dictionary": PageTypes.DictionaryPage,
    "QuestionAnswer": PageTypes.QAPage,
    "Quiz": PageTypes.QuizPage,
}


@pytest.fixture
def database():
    db = Database()
    db.fetch()
    try:
        yield db
    finally:
        db.connection.close()


@pytest.mark.parametrize("name,expected_id", [(key, value) for key, value in constants.items()])
def test_page_types_constants(database, name, expected_id):
    assert database.page_types[expected_id].name == name


test = {
    'html': """<table>
<tbody>
<tr>
<td>
<p>L. P</p>
</td>
<td>&nbsp;</td>
<td>
<p>PRAWDA</p>
</td>
<td>
<p>FAŁSZ</p>
</td>
</tr>
<tr>
<td>
<p>1.</p>
</td>
<td>
<p>Traktat w Verdun został podpisany w 814 r.</p>
</td>
<td>&nbsp;</td>
<td>
<p>F</p>
</td>
</tr>
<tr>
<td>
<p>2.</p>
</td>
<td>
<p>Królestwo Wschodniofrankońskie dostało się pod władzę Lotara Niemca</p>
</td>
<td>&nbsp;</td>
<td>
<p>F</p>
</td>
</tr>
<tr>
<td>
<p>3.</p>
</td>
<td>
<p>Ludwik Dziecię to ostatni władca z dynastii Karolingów niemieckich</p>
</td>
<td>
<p>P</p>
</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>
<p>4.</p>
</td>
<td>
<p>Pierwszym władcą elekcyjnym w Niemczech był Konrad I Frankoński</p>
</td>
<td>
<p>P</p>
</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>
<p>5.</p>
</td>
<td>
<p>Czechy stały się częścią Rzeszy Niemieckiej w 929 r.</p>
</td>
<td>
<p>P</p>
</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>
<p>6.</p>
</td>
<td>
<p>Otton I został cesarzem rzymskim w 962 r.</p>
</td>
<td>
<p>P</p>
</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>
<p>7.</p>
</td>
<td>
<p>W 962 r. Otton pierwszy ogłosił w Rzymie doktrynę papocezaryzmu</p>
</td>
<td>&nbsp;</td>
<td>
<p>F</p>
</td>
</tr>
<tr>
<td>
<p>8.</p>
</td>
<td>
<p>Wielka Wędrówka Ludów zakończyła się na skutek pokonania Madziarów pod Regnicą</p>
</td>
<td>&nbsp;</td>
<td>
<p>F</p>
</td>
</tr>
<tr>
<td>
<p>9.</p>
</td>
<td>
<p>Henryk I Ptasznik pochodził z dynastii saskich Ludolfingów</p>
</td>
<td>
<p>P</p>
</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>
<p>10.</p>
</td>
<td>
<p>Adelajda Burgundzka wniosła w posagu Ottonowi I koronę Longobardów</p>
</td>
<td>
<p>P</p>
</td>
<td>&nbsp;</td>
</tr>
</tbody>
</table>""",

    'res': [
        ['Cesarz Otton III, pod wpływem swojej matki, chciał stworzyć uniwersalne cesarstwo', True],
        ['Uniwersalne cesarstwo Ottona III miało się składać z Italii, Germanii, Galii', False],
        ['Konkordat to umowa między Państwem Kościelnym, a państwem świeckim', True],
        ['Konkordat wormacki został podpisany w 1122 r.', True],
        ['Konkordat wormacki podpisał papież Grzegorz VII i papież Kalikst II', False],
        ['Canossa to miejsce upokorzenia się cesarza Henryka V przed papieżem Grzegorzem VII', False],
        ['Cesarz Otton III odbył pielgrzymkę do grobu św. Wojciecha w Gnieźnie', True],
        [
            'Pierwszy etap walki między papiestwem a cesarstwem o prawo do mianowania biskupów nazywał się walką o inwestyturę',
            True]
    ]
}


def converter(html):
    return [['elo', False]]


@pytest.mark.parametrize(test)
def test_page_types_constants(dictionary):
    assert converter(dictionary['html']) == dictionary['res']
