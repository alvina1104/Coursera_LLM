from sqladmin import ModelView
from mysite.database.models import User, RefreshToken, Category, Course, StudyGroup, Application, Enrollment


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.full_name, User.email, User.role, User.is_active]
    column_searchable_list = [User.full_name, User.email]
    column_sortable_list = [User.id, User.email, User.created_at]


class RefreshTokenAdmin(ModelView, model=RefreshToken):
    column_list = [RefreshToken.id, RefreshToken.user_id, RefreshToken.expires_at, RefreshToken.is_revoked, RefreshToken.created_at]


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.category_name]
    column_searchable_list = [Category.category_name]


class CourseAdmin(ModelView, model=Course):
    column_list = [Course.id, Course.title, Course.category_id, Course.price, Course.duration_weeks, Course.status, Course.is_active]
    column_searchable_list = [Course.title]


class StudyGroupAdmin(ModelView, model=StudyGroup):
    column_list = [StudyGroup.id, StudyGroup.name, StudyGroup.course_id, StudyGroup.teacher_id, StudyGroup.starts_on, StudyGroup.ends_on, StudyGroup.status]
    column_searchable_list = [StudyGroup.name]


class ApplicationAdmin(ModelView, model=Application):
    column_list = [Application.id, Application.student_id, Application.course_id, Application.manager_id, Application.status, Application.created_at]


class EnrollmentAdmin(ModelView, model=Enrollment):
    column_list = [Enrollment.id, Enrollment.student_id, Enrollment.group_id, Enrollment.status, Enrollment.created_at]