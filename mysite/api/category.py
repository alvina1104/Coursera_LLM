from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import Category, User, RoleChoices
from mysite.database.schema import CategoryInputSchema, CategoryUpdateSchema, CategoryOutputSchema


category_router = APIRouter(prefix="/categories", tags=["Categories"])


@category_router.post("/", response_model=CategoryOutputSchema)
async def create_category(category: CategoryInputSchema, db: Session = Depends(get_db), current_admin: User = Depends(get_current_user)):
    if current_admin.role != RoleChoices.admin:
        raise HTTPException(status_code=403, detail="Только admin может создать category")
    category_data = Category(category_name=category.category_name)
    db.add(category_data)
    db.commit()
    db.refresh(category_data)
    return category_data


@category_router.get("/", response_model=list[CategoryOutputSchema])
async def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@category_router.get("/{category_id}", response_model=CategoryOutputSchema)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail="Такого категория не найдена")

    return category


@category_router.put("/{category_id}", response_model=CategoryOutputSchema)
async def update_category(category_id: int, category: CategoryUpdateSchema, db: Session = Depends(get_db), current_admin: User = Depends(get_current_user)):
    if current_admin.role != RoleChoices.admin:
        raise HTTPException(status_code=403, detail="Только admin может изменить category")
    category_db = db.query(Category).filter(Category.id == category_id).first()

    if not category_db:
        raise HTTPException(status_code=404, detail="Такого категория не найдена")

    for key, value in category.model_dump(exclude_unset=True).items():
        setattr(category_db, key, value)

    db.commit()
    db.refresh(category_db)
    return category_db


@category_router.delete("/{category_id}")
async def delete_category(category_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_user)):
    if current_admin.role != RoleChoices.admin:
        raise HTTPException(status_code=403, detail="Только admin может удалить category")
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail="Такого категория не найдена")

    db.delete(category)
    db.commit()

    return {"message": "Category успешно удалена"}