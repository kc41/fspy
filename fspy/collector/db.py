from sqlalchemy import Column, String, BigInteger, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DiffReport(Base):
    __tablename__ = 'diff_reports'

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    source_name = Column(String)
