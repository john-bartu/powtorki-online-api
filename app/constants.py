class KnowledgeTypes:
    History = 1
    Civics = 2


class PageTypes:
    Page = 1
    DocumentPage = 2
    ScriptPage = 3
    CharacterPage = 4
    CalendarPage = 5
    DictionaryPage = 6
    QAPage = 7
    QuizPage = 8
    MindmapPage = 9
    VideoScriptPage = 10


class TaxonomyTypes:
    Taxonomy = 1
    SubjectTaxonomy = 2
    ChapterTaxonomy = 3
    SetTaxonomy = 4
    KindTaxonomy = 5


class Roles:
    Admin = 'admin'
    User = 'user'
    map_id_to_name = {
        1: "admin",
        2: 'user',
    }
