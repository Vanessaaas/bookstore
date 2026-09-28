"""Реестр заказов: просмотр, смена статуса и даты доставки."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order, OrderStatus, User
from ..schemas import OrderItemOut, OrderOut, OrderUpdate
from ..security import ROLE_ADMIN, ROLE_MANAGER, require_roles

router = APIRouter(prefix="/api/orders", tags=["orders"])

managers = require_roles(ROLE_MANAGER, ROLE_ADMIN)


def to_out(order: Order, today: date) -> OrderOut:
    return OrderOut(
        id=order.id,
        order_date=order.order_date,
        delivery_date=order.delivery_date,
        client=order.client.full_name,
        status_id=order.status_id,
        status=order.status.name,
        # Просрочка: дата доставки прошла, а заказ не выполнен (статус не финальный)
        is_overdue=order.delivery_date < today and not order.status.is_final,
        items=[
            OrderItemOut(article=i.book.article, title=i.book.title, quantity=i.quantity)
            for i in sorted(order.items, key=lambda i: i.book.article)
        ],
    )


@router.get("", response_model=list[OrderOut])
def list_orders(_: User = Depends(managers), db: Session = Depends(get_db)):
    today = date.today()
    orders = db.scalars(select(Order).order_by(Order.id)).unique()
    return [to_out(o, today) for o in orders]


@router.patch("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: int,
    data: OrderUpdate,
    _: User = Depends(managers),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "Заказ не найден")
    if db.get(OrderStatus, data.status_id) is None:
        raise HTTPException(422, "Такого статуса не существует")
    if data.delivery_date < order.order_date:
        raise HTTPException(422, "Дата доставки не может быть раньше даты оформления")
    order.status_id = data.status_id
    order.delivery_date = data.delivery_date
    db.commit()
    db.refresh(order)
    return to_out(order, date.today())
