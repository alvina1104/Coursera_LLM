from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import StudyGroup, Course, Enrollment, User, RoleChoices, GroupStatus, EnrollmentStatus
from mysite.database.schema import StudyGroupInputSchema, StudyGroupUpdateSchema, StudyGroupOutputSchema
from mysite.api.auth import get_current_user

studygroup_router = APIRouter(prefix="/study-groups", tags=["Study Groups"])


@studygroup_router.post("/", response_model=StudyGroupOutputSchema)
async def create_study_group(group: StudyGroupInputSchema, db: Session = Depends(get_db), current_teacher: User = Depends(get_current_user)):
    if current_teacher.role != RoleChoices.teacher:
        raise HTTPException(status_code=403, detail="Только teacher может создавать study group")

    course = db.query(Course).filter(Course.id == group.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")

    if group.capacity <= 0:
        raise HTTPException(status_code=400, detail="Количество мест должно быть больше 0")

    if group.starts_on >= group.ends_on:
        raise HTTPException(status_code=400, detail="Дата окончания должна быть позже даты начала")

    group_data = StudyGroup(
        name=group.name, course_id=group.course_id, teacher_id=current_teacher.id,
        starts_on=group.starts_on, ends_on=group.ends_on, capacity=group.capacity,
        status=GroupStatus.recruiting
    )

    db.add(group_data)
    db.commit()
    db.refresh(group_data)
    return group_data


@studygroup_router.get("/", response_model=list[StudyGroupOutputSchema])
async def get_study_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(StudyGroup).all()


@studygroup_router.get("/{group_id}", response_model=StudyGroupOutputSchema)
async def get_study_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Учебная группа не найдена")
    return group


@studygroup_router.put("/{group_id}", response_model=StudyGroupOutputSchema)
async def update_study_group(group_id: int, group: StudyGroupUpdateSchema, db: Session = Depends(get_db), current_teacher: User = Depends(get_current_user)):
    if current_teacher.role != RoleChoices.teacher:
        raise HTTPException(status_code=403, detail="Только teacher может изменять study group")

    group_db = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not group_db:
        raise HTTPException(status_code=404, detail="Учебная группа не найдена")

    if group_db.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Вы можете изменять только свои группы")

    data = group.model_dump(exclude_unset=True)
    if "capacity" in data:
        enrolled = db.query(Enrollment).filter(
            Enrollment.group_id == group_id,
            Enrollment.status == EnrollmentStatus.active
        ).count()
        if data["capacity"] <= 0 or data["capacity"] < enrolled:
            raise HTTPException(status_code=400, detail="Нельзя установить вместимость меньше числа записанных студентов")

    if "starts_on" in data and "ends_on" in data:
        if data["starts_on"] >= data["ends_on"]:
            raise HTTPException(status_code=400, detail="Дата окончания должна быть позже даты начала")

    for key, value in data.items():
        setattr(group_db, key, value)

    db.commit()
    db.refresh(group_db)
    return group_db


@studygroup_router.delete("/{group_id}")
async def delete_study_group(group_id: int, db: Session = Depends(get_db), current_teacher: User = Depends(get_current_user)):
    if current_teacher.role != RoleChoices.teacher:
        raise HTTPException(status_code=403, detail="Только teacher может удалять study group")

    group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Учебная группа не найдена")

    if group.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Вы можете удалять только свои группы")

    if db.query(Enrollment).filter(Enrollment.group_id == group_id).first():
        raise HTTPException(status_code=400, detail="Нельзя удалить группу, в которой есть записи студентов")

    db.delete(group)
    db.commit()
    return {"message": "Учебная группа успешно удалена"}