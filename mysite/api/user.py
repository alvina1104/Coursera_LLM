from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import User, RoleChoices
from mysite.database.schema import UserInputSchema, UserOutputSchema, UserUpdateSchema
from mysite.api.auth import get_password_hash
from langchain_core.tools import tool


user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post("/")
async def create_user(data: UserInputSchema, db: Session = Depends(get_db)):
    user = User(
        full_name=data.full_name,
        email=data.email,
        password=get_password_hash(data.password),
        role=data.role,
        is_active=False
        )
    db.add(user)
    db.commit()
    return {"message": "Вы успешно зарегистрировались"}


@user_router.get("/", response_model=list[UserOutputSchema])
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@user_router.get("/{user_id}/", response_model=UserOutputSchema)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@user_router.put("/{user_id}/")
async def update_user(user_id: int, data: UserUpdateSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    return {"message": "Данные успешно обновлены"}


@user_router.delete("/{user_id}/")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(user)
    db.commit()
    return {"message": "Пользователь успешно удалён"}



def build_user_tools(db: Session, current_user: User):
    @tool
    def get_my_profile(user_id: int | None = None) -> dict:
        """Профиль текущего пользователя. Если пользователь называет чужой id, передай его в user_id."""
        if user_id is not None and user_id != current_user.id:
            return {"error": "Я могу получить только профиль пользователя, авторизованного в текущем запросе."}
        user = current_user
        return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role.value,
                "is_active": user.is_active, "created_at": user.created_at.isoformat()}

    # @tool
    # def update_my_profile(full_name: str | None = None, email: str | None = None) -> dict:
    #     """Изменить ФИО и/или email текущего пользователя."""
    #     if email and db.query(User).filter(User.email == email, User.id != current_user.id).first():
    #         return {"error": "Этот email уже занят"}
    #     if full_name:
    #         current_user.full_name = full_name
    #     if email:
    #         current_user.email = email
    #     db.commit()
    #     return {"message": "Данные успешно обновлены"}

    @tool
    def delete_my_account(confirm: bool = False) -> dict:
        """Удалить аккаунт. Только после явного подтверждения (confirm=True)."""
        if not confirm:
            return {"error": "Нужно подтверждение"}
        db.delete(current_user)
        db.commit()
        return {"message": "Аккаунт успешно удалён"}

    @tool
    def register_user(full_name: str, email: str, password: str) -> dict:
        """Зарегистрировать нового студента."""
        if db.query(User).filter(User.email == email).first():
            return {"error": "Этот email уже занят"}
        db.add(User(
            full_name=full_name,
            email=email,
            password=get_password_hash(password),
            role=RoleChoices.student,
        ))
        db.commit()
        return {"message": "Вы успешно зарегистрировались"}

    return [get_my_profile]
    # return [get_my_profile, update_my_profile, delete_my_account, register_user]