from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from mysite.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME
from mysite.database.db import get_db
from mysite.database.models import User, RefreshToken
from mysite.database.schema import UserInputSchema, UserOutputSchema, ChangePasswordSchema, UserLoginSchema, VerifyOutputSchema


credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не удалось проверить учетные данные", headers={"WWW-Authenticate": "Bearer"})
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/")
auth_router = APIRouter(prefix="/auth", tags=["Auth"])


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_LIFETIME))
    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_LIFETIME)
    to_encode.update({"exp": expire, "token_type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("token_type") != "access":
            raise credentials_exception

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise credentials_exception

    return user


def get_token_data(user: User):
    return {"sub": str(user.id), "full_name": user.full_name, "role": user.role.value}


@auth_router.post("/register/")
async def register(user: UserInputSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email уже существует")

    user_data = User(
        full_name=user.full_name,
        email=user.email,
        password=get_password_hash(user.password),
        role=user.role,
        is_active=False
    )

    db.add(user_data)
    db.commit()
    db.refresh(user_data)

    return {"message": "Вы успешно создали аккаунт"}


@auth_router.post("/login/")
async def login(data: UserLoginSchema, db: Session = Depends(get_db)):
    user_db = db.query(User).filter(User.email == data.email).first()

    if not user_db or not verify_password(data.password, user_db.password):
        raise HTTPException(status_code=401, detail="Email или password неправильный")


    token_data = get_token_data(user_db)
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    db.add(RefreshToken(
        user_id=user_db.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_LIFETIME)
    ))
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }


@auth_router.post("/logout/")
async def logout(refresh_token: str = Query(...), db: Session = Depends(get_db)):
    token_db = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()

    if not token_db:
        raise HTTPException(status_code=401, detail="Неверный refresh token")

    db.delete(token_db)
    db.commit()

    return {"message": "Пользователь успешно вышел из системы"}


@auth_router.post("/refresh/")
async def refresh(refresh_token: str = Query(...), db: Session = Depends(get_db)):
    token_db = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()

    if not token_db:
        raise HTTPException(status_code=401, detail="Неверный refresh token")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("token_type") != "refresh":
            raise HTTPException(status_code=401, detail="Неверный тип токена")

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token недействителен или срок его действия истёк")

    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise credentials_exception

    access_token = create_access_token(get_token_data(user))

    return {"access_token": access_token, "token_type": "Bearer"}


@auth_router.get("/me/", response_model=UserOutputSchema)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@auth_router.get("/verify/", response_model=VerifyOutputSchema)
async def verify(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "role": current_user.role
    }


@auth_router.post("/change-password/")
async def change_password(data: ChangePasswordSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Старый пароль неправильный")

    current_user.password = get_password_hash(data.new_password)
    db.commit()

    return {"message": "Пароль успешно изменён"}