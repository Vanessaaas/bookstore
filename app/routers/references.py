"""Справочники для выпадающих списков."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Author, Genre, OrderStatus, Publisher, User
from ..schemas import RefItem
from ..security import ROLE_ADMIN, ROLE_MANAGER, ROLE_SELLER, require_roles

router = APIRouter(prefix="/api", tags=["references"])

staff = require_roles(ROLE_SELLER, ROLE_MANAGER, ROLE_ADMIN)


@router.get("/genres", response_model=list[RefItem])
def genres(_: User = Depends(staff), db: Session = Depends(get_db)):
    return [RefItem(id=g.id, name=g.name) for g in db.scalars(select(Genre).order_by(Genre.name))]


@router.get("/publishers", response_model=list[RefItem])
def publishers(_: User = Depends(staff), db: Session = Depends(get_db)):
    rows = db.scalars(select(Publisher).order_by(Publisher.name))
    return [RefItem(id=p.id, name=p.name) for p in rows]


@router.get("/authors", response_model=list[RefItem])
def authors(_: User = Depends(staff), db: Session = Depends(get_db)):
    rows = db.scalars(select(Author).order_by(Author.full_name))
    return [RefItem(id=a.id, name=a.full_name) for a in rows]


@router.get("/order-statuses", response_model=list[RefItem])
def order_statuses(
    _: User = Depends(require_roles(ROLE_MANAGER, ROLE_ADMIN)), db: Session = Depends(get_db)
):
    rows = db.scalars(select(OrderStatus).order_by(OrderStatus.id))
    return [RefItem(id=s.id, name=s.name) for s in rows]
