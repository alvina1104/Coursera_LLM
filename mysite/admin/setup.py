from sqladmin import Admin
from mysite.database.db import engine
from mysite.admin.view import UserAdmin, RefreshTokenAdmin, CategoryAdmin, CourseAdmin, StudyGroupAdmin, ApplicationAdmin, EnrollmentAdmin

def setup_admin(app):
    admin = Admin(app, engine, title="Coursera Admin")

    admin.add_view(UserAdmin)
    admin.add_view(RefreshTokenAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(CourseAdmin)
    admin.add_view(StudyGroupAdmin)
    admin.add_view(ApplicationAdmin)
    admin.add_view(EnrollmentAdmin)

    return admin