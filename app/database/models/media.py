import json

from sqlalchemy import Column, Integer, VARCHAR, String

from app.database.database import Base


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(VARCHAR(80))
    description = Column(VARCHAR(180))
    path = Column(VARCHAR(255))
    author = Column(VARCHAR(255))
    licence = Column(VARCHAR(100))
    slug = Column(VARCHAR(80))
    mime_type = Column(VARCHAR(30))

    time_creation = Column(String)
    time_edited = Column(String)

    def __repr__(self):
        filter_names = ['id', 'name', 'description', 'path', 'author', 'licence', 'slug', 'mime_type']
        return json.dumps({index: str(value) if index in filter_names else "" for index, value in vars(self).items()})
