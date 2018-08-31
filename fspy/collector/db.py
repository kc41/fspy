from typing import Optional

from sqlalchemy import Column, String, BigInteger, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

import enum

from sqlalchemy.orm import relationship

from fspy.common import model

Base = declarative_base()


class OperationsEnum(enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class DiffReport(Base):
    __tablename__ = 'diff_reports'

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)

    run_start = Column(DateTime(timezone=True), index=True)
    run_end = Column(DateTime(timezone=True), index=True)

    source_name = Column(String(), index=True)
    source_ip = Column(String(), nullable=True, index=True)

    diff_list = relationship("FileDiff", back_populates="diff_report")


class FileDiff(Base):
    __tablename__ = 'file_diffs'

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)

    diff_report_id = Column(BigInteger(), ForeignKey(DiffReport.id, name="fk_diff_report_id"))

    diff_report = relationship(DiffReport, back_populates="diff_list")

    file_path = Column(String())
    operation = Column(Enum(OperationsEnum))

    size_before = Column(BigInteger(), nullable=True)
    size_after = Column(BigInteger(), nullable=True)

    operation_time = Column(DateTime(timezone=True), index=True)


def diff_report_to_db_model(dr: model.DiffReport, source_ip: Optional[str] = None) -> DiffReport:
    diff_report = DiffReport(
        source_name=dr.source_name,
        source_ip=source_ip,

        run_start=dr.diff.run_start,
        run_end=dr.diff.run_end,
    )

    for file_state in dr.diff.created:
        FileDiff(
            diff_report=diff_report,
            file_path=file_state.path,

            operation=OperationsEnum.CREATE,
            size_after=file_state.size,

            operation_time=file_state.date_created
        )

    for file_diff in dr.diff.updated:
        FileDiff(
            diff_report=diff_report,
            file_path=file_diff.before.path,

            operation=OperationsEnum.UPDATE,
            size_before=file_diff.before.size,
            size_after=file_diff.after.size,

            operation_time=file_diff.after.date_updated,
        )

    for file_state in dr.diff.deleted:
        FileDiff(
            diff_report=diff_report,
            file_path=file_state.path,

            operation=OperationsEnum.DELETE,
            size_before=file_state.size,

            operation_time=dr.diff.run_start,
            # operation_time=dr.diff.run_end,
        )

    return diff_report
