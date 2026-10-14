from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Course, User, RoleChoices
from mysite.database.schema import CourseInputSchema, CourseUpdateSchema, CourseOutputSchema
from mysite.api.auth import get_current_user


course_router = APIRouter(prefix="/courses", tags=["Courses"])


@course_router.post("/", response_model=CourseOutputSchema)
async def create_course(course: CourseInputSchema, db: Session = Depends(get_db), current_teacher: User = Depends(get_current_user)):
    if current_teacher.role != RoleChoices.teacher:
        raise HTTPException(status_code=403, detail="Только teacher может создать курсы")

    course_data = Course(
        title=course.title,
        category_id=course.category_id,
        description=course.description,
        level=course.level,
        price=course.price,
        duration_weeks=course.duration_weeks,
        status=course.status
    )

    db.add(course_data)
    db.commit()
    db.refresh(course_data)

    return course_data


@course_router.get("/", response_model=list[CourseOutputSchema])
async def get_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()


@course_router.get("/{course_id}", response_model=CourseOutputSchema)
async def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@course_router.put("/{course_id}", response_model=CourseOutputSchema)
async def update_course(course_id: int, course: CourseUpdateSchema, db: Session = Depends(get_db), current_teacher: User = Depends(get_current_user)):
    if current_teacher.role != RoleChoices.teacher:
        raise HTTPException(status_code=403, detail="Только teacher может изменить курсы")
    
    course_db = db.query(Course).filter(Course.id == course_id).first()
    if not course_db:
        raise HTTPException(status_code=404, detail="Такого курсы нету")

    for key, value in course.model_dump(exclude_unset=True).items():
        setattr(course_db, key, value)

    db.commit()
    db.refresh(course_db)

    return course_db


@course_router.delete("/{course_id}")
async def delete_course(course_id: int, db: Session = Depends(get_db), current_teacher: User = Depends(get_current_user)):
    if current_teacher.role != RoleChoices.teacher:
        raise HTTPException(status_code=403, detail="Только teacher может удалить курсы")
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.delete(course)
    db.commit()

    return {"message": "Course успешно удален"}