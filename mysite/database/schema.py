from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field, field_validator
from mysite.database.models import (RoleChoices,LevelChoices,CourseStatus,
                                    GroupStatus,ApplicationStatus,EnrollmentStatus)



class UserInputSchema(BaseModel):
    full_name: str
    email: str
    password: str
    role: RoleChoices = RoleChoices.student


class UserOutputSchema(BaseModel):
    id: int
    full_name: str
    email: str
    role: RoleChoices
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdateSchema(BaseModel):
    full_name: str | None = None
    email: str | None = None
    role: RoleChoices | None = None
    is_active: bool | None = None


class UserLoginSchema(BaseModel):
    email: str
    password: str


class VerifyOutputSchema(BaseModel):
    user_id: int
    full_name: str
    role: RoleChoices


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str


class RefreshTokenInputSchema(BaseModel):
    user_id: int
    token: str
    expires_at: datetime


class RefreshTokenOutputSchema(BaseModel):
    id: int
    user_id: int
    token: str
    expires_at: datetime
    is_revoked: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class CategoryInputSchema(BaseModel):
    category_name: str


class CategoryOutputSchema(BaseModel):
    id: int
    category_name: str

    model_config = ConfigDict(from_attributes=True)


class CategoryUpdateSchema(BaseModel):
    category_name: str



class CourseInputSchema(BaseModel):
    title: str
    category_id: int
    description: str
    level: list[LevelChoices] = Field(min_length=1,max_length=3)
    price: int
    duration_weeks: int
    status: CourseStatus = CourseStatus.free

    @field_validator("level")
    @classmethod
    def validate_level(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Levels must be unique")
        return value


class CourseOutputSchema(BaseModel):
    id: int
    title: str
    category_id: int
    description: str
    level: list[LevelChoices]
    price: int
    duration_weeks: int
    is_active: bool
    status: CourseStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseUpdateSchema(BaseModel):
    title: str | None = None
    category_id: int | None = None
    description: str | None = None
    level: list[LevelChoices] | None = Field(
        default=None,
        min_length=1,
        max_length=3
    )
    price: int | None = None
    duration_weeks: int | None = None
    is_active: bool | None = None
    status: CourseStatus | None = None

    @field_validator("level")
    @classmethod
    def validate_level(cls, value):
        if value is not None and len(value) != len(set(value)):
            raise ValueError("Levels must be unique")
        return value



class StudyGroupInputSchema(BaseModel):
    name: str
    course_id: int
    starts_on: date
    ends_on: date
    capacity: int


class StudyGroupOutputSchema(BaseModel):
    id: int
    name: str
    course_id: int
    teacher_id: int
    starts_on: date
    ends_on: date
    capacity: int
    status: GroupStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



class StudyGroupUpdateSchema(BaseModel):
    name: str | None = None
    course_id: int | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    capacity: int | None = None
    status: GroupStatus | None = None



class ApplicationInputSchema(BaseModel):
    course_id: int
    comment: str | None = None


class ApplicationOutputSchema(BaseModel):
    id: int
    student_id: int
    course_id: int
    manager_id: int | None
    comment: str | None
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationUpdateSchema(BaseModel):
    comment: str | None = None
    status: ApplicationStatus | None = None



class EnrollmentInputSchema(BaseModel):
    student_id: int
    group_id: int


class EnrollmentOutputSchema(BaseModel):
    id: int
    student_id: int
    group_id: int
    status: EnrollmentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnrollmentUpdateSchema(BaseModel):
    status: EnrollmentStatus