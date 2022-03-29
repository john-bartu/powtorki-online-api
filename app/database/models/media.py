import json

from sqlalchemy import Column, Integer, VARCHAR, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.render.templater import render_template


class PageMedia(Base):
    __tablename__ = "v_page_media"

    id = Column(Integer, primary_key=True, index=True)
    id_page = Column(Integer, ForeignKey("pages.id"))
    id_media = Column(Integer, ForeignKey("media.id"))
    name = Column(VARCHAR(80))
    path = Column(VARCHAR(255))
    mime_type = Column(VARCHAR(30))


class MapPageMedia(Base):
    __tablename__ = "map_page_media"

    id = Column(Integer, primary_key=True, index=True)
    id_page = Column(Integer, ForeignKey("pages.id"))
    id_media = Column(Integer, ForeignKey("media.id"))

    media = relationship('Media', uselist=False)
    page = relationship('Page', uselist=False)


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

    def format(self):
        return render_template('image-box.html', SOURCE=self.path)

    def __repr__(self):
        filter_names = ['id', 'name', 'description', 'path', 'author', 'licence', 'slug', 'mime_type']
        return json.dumps({index: str(value) if index in filter_names else "" for index, value in vars(self).items()})
