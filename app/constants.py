class KnowledgeTypes:
    History = 1
    Civics = 2


class PageTypes:
    """
    Defines page handling logic
    """
    Page = 1
    DocumentPage = 2
    CharacterPage = 4
    CalendarPage = 5
    DictionaryPage = 6
    QAPage = 7
    QuizPage = 8


class PageSubTypes:
    """
    Defines variants of page types (same logic different scope)
    """
    VideoScriptPage = 1
    # ProofPage = 2
    # ExperimentPage = 3
    MindmapPage = 4
    ScriptPage = 5
    DocumentPage = 6
    Character = 7
    Date = 8
    Dictionary = 9
    QA = 10
    Quiz = 11
    # TheoremPage = 12


class TaxonomyTypes:
    """
    Defines taxonomy logic scope
    """
    Taxonomy = 1
    SubjectTaxonomy = 2
    ChapterTaxonomy = 3
    SetTaxonomy = 4


class Roles:
    Admin = 'admin'
    User = 'user'
    map_id_to_name = {
        1: "admin",
        2: 'user',
    }

    # fastapi_permissions principal for the admin role, e.g. used in ACLs as
    # (Allow, Roles.AdminPrincipal, All). Matches the "role:{name}" principals
    # minted in app.routers.auth.login_for_access_token.
    AdminPrincipal = f"role:{Admin}"


class ActivitySettings:
    correct_answer = 1
    incorrect_answer = -2
    page_read = 0.25


class LearningSettings:
    """Tuning constants for Learning Mode (TestSession) chunk selection."""
    chunk_size = 5
    streak_cap = 3
    # Days a page stays "not due" after N consecutive correct grades (Leitner-style).
    interval_days = {0: 0, 1: 1, 2: 3, 3: 7}
    # Relative sampling weight by streak — lower streak = seen more often.
    base_weight = {0: 5, 1: 3, 2: 2, 3: 1}
    # Flashcard-graded (swipe/button, self-reported known/unknown) page types.
    flashcard_types = {PageTypes.CharacterPage, PageTypes.CalendarPage,
                        PageTypes.DictionaryPage, PageTypes.QAPage}
