from sqlalchemy import Column, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DiffReport(Base):
    __tablename__ = 'diff_reports'

    id = Column(BigInteger, primary_key=True)
    source_name = Column(String)
