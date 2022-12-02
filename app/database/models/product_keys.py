from sqlalchemy import Column, Integer, VARCHAR, ForeignKey

from app.database.database import Base


class ProductKeys(Base):
    __tablename__ = "product_keys"
    id = Column(Integer, primary_key=True, index=True)
    id_taxonomy = Column(Integer, ForeignKey("taxonomies.id"))
    key = Column(VARCHAR(20))


class MapUserProductKey(Base):
    __tablename__ = "map_user_product_key"
    id = Column(Integer, primary_key=True, index=True)
    id_product_key = Column(Integer, ForeignKey("product_keys.id"))
    id_user = Column(Integer, ForeignKey("users.id"))
