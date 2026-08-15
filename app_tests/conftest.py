import pytest
from sqlalchemy import event

from app.database.database import SessionLocal, engine


@pytest.fixture
def db_session():
    """A DB session bound to one connection, wrapped in an outer transaction that is
    always rolled back at teardown -- regardless of how many times the code under
    test calls .commit().

    Services under test (TestSessionService, FlashcardService, QuizService, ...) call
    session.commit() as part of normal operation. A plain "begin/rollback" wouldn't
    survive that, since commit() would end the transaction early. Instead this uses
    the standard SQLAlchemy "join a session into an external transaction" recipe:
    open a SAVEPOINT (begin_nested) and restart it every time it gets closed by an
    inner commit, so nothing is ever actually released except by the final rollback
    of the real, outer transaction.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = SessionLocal(bind=connection)

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()
