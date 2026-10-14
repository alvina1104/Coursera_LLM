from mysite.database.db import SessionLocal
from mysite.database.models import Course

def get_active_courses():
    db = SessionLocal()

    try:
        return db.query(Course).filter(Course.is_active.is_(True)).all()
    finally:
        db.close()


def list_courses():
    return get_active_courses()


def search_courses(query: str):
    courses = get_active_courses()
    words = query.casefold().split()

    return [
        course for course in courses
        if any(
            word in course.title.casefold()
            or word in (course.description or "").casefold()
            for word in words
            if len(word) > 2
        )
    ]


def filter_courses(
        level: str | None = None,
        status: str | None = None,
        max_price: int | None = None
):
    courses = get_active_courses()
    result = []

    for course in courses:
        if level and level not in [
            item.value if hasattr(item, "value") else item
            for item in (course.level or [])
        ]:
            continue
        course_status = (
            course.status.value
            if hasattr(course.status, "value")
            else course.status
        )
        if status and course_status != status:
            continue

        if max_price is not None and course.price > max_price:
            continue

        result.append(course)
    return  result


def compare_courses(course_ids: list[int]):
    db = SessionLocal()

    try:
        return db.query(Course).filter(
            Course.id.in_(course_ids),
            Course.is_active.is_(True)
        ).all()
    finally:
        db.close()

def recommend_courses(
        level: str | None = None,
        max_price: int | None = None
):
    courses = filter_courses(
        level=level,
        max_price=max_price,
    )
    return courses[:5]
