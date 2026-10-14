from sqlalchemy import String, Integer, Boolean, Date, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from mysite.database.db import Base
from enum import Enum as PyEnum


class RoleChoices(str, PyEnum):
     student = "student"
     teacher = "teacher"
     manager = "manager"
     admin = "admin"


class LevelChoices(str, PyEnum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class CourseStatus(str, PyEnum):
    free = "free"
    plus = "plus"


class GroupStatus(str, PyEnum):
    recruiting = "recruiting"
    active= "active"
    completed = "completed"
    cancelled = "cancelled"


class ApplicationStatus(str, PyEnum):
    new = "new"
    in_progress = "in_progress"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


class EnrollmentStatus(str, PyEnum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(50), unique=True)
    password: Mapped[str] = mapped_column(String(50))
    role: Mapped[RoleChoices] = mapped_column(Enum(RoleChoices), default=RoleChoices.student)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    teaching_groups: Mapped[list["StudyGroup"]] = relationship(back_populates="teacher")
    applications: Mapped[list["Application"]] = relationship(foreign_keys="Application.student_id", back_populates="student")
    managed_applications: Mapped[list["Application"]] = relationship(foreign_keys="Application.manager_id", back_populates="manager")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")



class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(500), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String(100), unique=True)

    courses: Mapped[list["Course"]] = relationship(back_populates="category")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(150))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    description: Mapped[str] = mapped_column(String(1000))
    level: Mapped[list[str]] = mapped_column(JSON)
    price: Mapped[int] = mapped_column(Integer, default=0)
    duration_weeks: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[CourseStatus] = mapped_column(Enum(CourseStatus),default=CourseStatus.free)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

    category: Mapped["Category"] = relationship(back_populates="courses")
    study_groups: Mapped[list["StudyGroup"]] = relationship(back_populates="course")

    applications: Mapped[list["Application"]] = relationship(back_populates="course")


class StudyGroup(Base):
    __tablename__ = "study_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[GroupStatus] = mapped_column(Enum(GroupStatus),default=GroupStatus.recruiting)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

    course: Mapped["Course"] = relationship(back_populates="study_groups")
    teacher: Mapped["User"] = relationship(back_populates="teaching_groups")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="group")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.new)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student: Mapped["User"] = relationship(foreign_keys=[student_id], back_populates="applications")
    manager: Mapped["User"] = relationship(foreign_keys=[manager_id], back_populates="managed_applications")
    course: Mapped["Course"] = relationship(back_populates="applications")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("study_groups.id"))
    status: Mapped[EnrollmentStatus] = mapped_column(Enum(EnrollmentStatus), default=EnrollmentStatus.active)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student: Mapped["User"] = relationship(back_populates="enrollments")
    group: Mapped["StudyGroup"] = relationship(back_populates="enrollments")