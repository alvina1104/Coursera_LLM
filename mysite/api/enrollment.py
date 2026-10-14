from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Enrollment, StudyGroup, Application, User, RoleChoices, EnrollmentStatus, ApplicationStatus, GroupStatus
from mysite.database.schema import EnrollmentInputSchema, EnrollmentOutputSchema
from mysite.api.auth import get_current_user

enrollment_router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@enrollment_router.post("/", response_model=EnrollmentOutputSchema)
async def create_enrollment(enrollment: EnrollmentInputSchema, db: Session = Depends(get_db), current_manager: User = Depends(get_current_user)):
    if current_manager.role != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может записывать студентов")

    group = db.query(StudyGroup).filter(StudyGroup.id == enrollment.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Учебная группа не найдена")

    if group.status != GroupStatus.recruiting:
        raise HTTPException(status_code=400, detail="Запись в эту группу закрыта")

    application = db.query(Application).filter(
        Application.student_id == enrollment.student_id,
        Application.course_id == group.course_id,
        Application.status == ApplicationStatus.accepted
    ).first()

    if not application:
        raise HTTPException(status_code=400, detail="Нет принятой заявки на этот курс")

    existing = db.query(Enrollment).filter(
        Enrollment.student_id == enrollment.student_id,
        Enrollment.group_id == enrollment.group_id,
        Enrollment.status == EnrollmentStatus.active
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Студент уже записан в эту группу")

    enrolled = db.query(Enrollment).filter(
        Enrollment.group_id == group.id,
        Enrollment.status == EnrollmentStatus.active
    ).count()

    if enrolled >= group.capacity:
        raise HTTPException(status_code=400, detail="В группе нет свободных мест")

    enrollment_data = Enrollment(
        student_id=enrollment.student_id,
        group_id=group.id,
        status=EnrollmentStatus.active
    )

    db.add(enrollment_data)
    db.commit()
    db.refresh(enrollment_data)
    return enrollment_data


@enrollment_router.get("/", response_model=list[EnrollmentOutputSchema])
async def get_enrollments(db: Session = Depends(get_db), current_student: User = Depends(get_current_user)):
    if current_student.role != RoleChoices.student:
        raise HTTPException(status_code=403, detail="Только student может просматривать свои записи")

    return db.query(Enrollment).filter(Enrollment.student_id == current_student.id).all()


@enrollment_router.get("/{enrollment_id}", response_model=EnrollmentOutputSchema)
async def get_enrollment(enrollment_id: int, db: Session = Depends(get_db), current_student: User = Depends(get_current_user)):
    if current_student.role != RoleChoices.student:
        raise HTTPException(status_code=403, detail="Только student может просматривать свои записи")

    enrollment = db.query(Enrollment).filter(
        Enrollment.id == enrollment_id,
        Enrollment.student_id == current_student.id
    ).first()

    if not enrollment:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    return enrollment