from __future__ import annotations

from datetime import datetime
import enum
from typing import Optional

from sqlalchemy import (
    String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, Text,
    Index, Float, func
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# -------------------------
# Enums
# -------------------------
class Role(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"


class EnrollmentStatus(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ProgressStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


# -------------------------
# Core domain
# -------------------------
class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    memberships: Mapped[list[Membership]] = relationship(
        "Membership",
        back_populates="organization",
        cascade="all,delete-orphan",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    memberships: Mapped[list[Membership]] = relationship(
        "Membership",
        back_populates="user",
        cascade="all,delete-orphan",
    )


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, name="role_enum", native_enum=True, validate_strings=True),
        nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="memberships")
    organization: Mapped[Organization] = relationship("Organization", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("user_id", "org_id", name="uq_user_org"),
        Index("ix_membership_org", "org_id"),
        Index("ix_membership_user", "user_id"),
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    kvk: Mapped[Optional[str]] = mapped_column(String(50))
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    email_domain: Mapped[Optional[str]] = mapped_column(String(255))  # bv. 'zorginstelling.nl'
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("org_id", "name", name="uq_company_org_name"),
    )


# -------------------------
# Trainingen
# -------------------------
class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(2000))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization: Mapped[Organization] = relationship("Organization")
    modules: Mapped[list[Module]] = relationship("Module", back_populates="training", cascade="all, delete-orphan")
    enrollments: Mapped[list[Enrollment]] = relationship("Enrollment", back_populates="training", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_training_org", "org_id"),)


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    training_id: Mapped[int] = mapped_column(ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_url: Mapped[Optional[str]] = mapped_column(String(1000))  # link naar Moodle/content
    order_index: Mapped[int] = mapped_column(Integer, default=1)
    duration_min: Mapped[int] = mapped_column(Integer, default=10)

    training: Mapped[Training] = relationship("Training", back_populates="modules")
    progresses: Mapped[list[Progress]] = relationship("Progress", back_populates="module", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("training_id", "order_index", name="uq_module_training_order"),
        Index("ix_module_training", "training_id"),
    )


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    training_id: Mapped[int] = mapped_column(ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[EnrollmentStatus] = mapped_column(
        SAEnum(EnrollmentStatus, name="enrollment_status_enum", native_enum=True, validate_strings=True),
        default=EnrollmentStatus.ASSIGNED,
        nullable=False,
    )
    assigned_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    training: Mapped[Training] = relationship("Training", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("user_id", "training_id", name="uq_enrollment_user_training"),
        Index("ix_enrollment_user", "user_id"),
        Index("ix_enrollment_training", "training_id"),
    )


class Progress(Base):
    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[ProgressStatus] = mapped_column(
        SAEnum(ProgressStatus, name="progress_status_enum", native_enum=True, validate_strings=True),
        default=ProgressStatus.NOT_STARTED,
        nullable=False,
    )
    percent: Mapped[float] = mapped_column(Float, default=0.0)          # 0.0..100.0
    score: Mapped[Optional[float]] = mapped_column(Float)               # 0..100 of None
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_event_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    module: Mapped[Module] = relationship("Module", back_populates="progresses")
    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "module_id", name="uq_progress_user_module"),
        Index("ix_progress_user", "user_id"),
        Index("ix_progress_module", "module_id"),
    )
