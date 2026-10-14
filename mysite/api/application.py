from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Application, Course, User, RoleChoices, ApplicationStatus
from mysite.database.schema import ApplicationInputSchema, ApplicationUpdateSchema, ApplicationOutputSchema
from mysite.api.auth import get_current_user

application_router = APIRouter(prefix="/applications", tags=["Applications"])


@application_router.post("/", response_model=ApplicationOutputSchema)
async def create_application(application: ApplicationInputSchema, db: Session = Depends(get_db), current_student: User = Depends(get_current_user)):
    if current_student.role != RoleChoices.student:
        raise HTTPException(status_code=403, detail="Только student может создавать заявки")

    course = db.query(Course).filter(Course.id == application.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")

    if not course.is_active:
        raise HTTPException(status_code=400, detail="Курс неактивен")

    application_data = Application(
        student_id=current_student.id,
        course_id=application.course_id,
        comment=application.comment,
        status=ApplicationStatus.new
    )

    db.add(application_data)
    db.commit()
    db.refresh(application_data)
    return application_data


@application_router.get("/", response_model=list[ApplicationOutputSchema])
async def get_applications(db: Session = Depends(get_db), current_manager: User = Depends(get_current_user)):
    if current_manager.role != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может просматривать заявки")
    return db.query(Application).all()


@application_router.get("/{application_id}", response_model=ApplicationOutputSchema)
async def get_application(application_id: int, db: Session = Depends(get_db), current_manager: User = Depends(get_current_user)):
    if current_manager.role != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может просматривать заявки")

    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return application


@application_router.put("/{application_id}", response_model=ApplicationOutputSchema)
async def update_application(application_id: int, application: ApplicationUpdateSchema, db: Session = Depends(get_db), current_manager: User = Depends(get_current_user)):
    if current_manager.role != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может изменять заявки")

    application_db = db.query(Application).filter(Application.id == application_id).first()
    if not application_db:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    data = application.model_dump(exclude_unset=True)
    data.pop("student_id", None)
    data.pop("course_id", None)
    data["manager_id"] = current_manager.id

    for key, value in data.items():
        setattr(application_db, key, value)

    db.commit()
    db.refresh(application_db)
    return application_db


@application_router.delete("/{application_id}")
async def delete_application(application_id: int, db: Session = Depends(get_db), current_manager: User = Depends(get_current_user)):
    if current_manager.role != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может удалять заявки")

    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    db.delete(application)
    db.commit()
    return {"message": "Заявка успешно удалена"}