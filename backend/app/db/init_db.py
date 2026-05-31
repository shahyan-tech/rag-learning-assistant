from app.db import models
from app.db.session import Base, DEFAULT_DB_PATH, engine


def create_db_and_tables() -> None:
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)