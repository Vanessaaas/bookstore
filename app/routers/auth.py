"""Авторизация сотрудников."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import LoginIn, LoginOut, UserOut
from ..security import create_token, current_user, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.login == data.login.strip()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Неверный логин или пароль")
    return LoginOut(
        token=create_token(user.id),
        user=UserOut(full_name=user.full_name, role=user.role.name),
    )


@router.get("/me", response_model=UserOut)
def me(user: User | None = Depends(current_user)):
    if user is None:
        raise HTTPException(401, "Требуется авторизация")
    return UserOut(full_name=user.full_name, role=user.role.name)
