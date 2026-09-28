"""ORM-модели. Структура совпадает с database/create_db.sql (3НФ)."""
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    login: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"))

    role: Mapped[Role] = relationship(lazy="joined")


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Publisher(Base):
    __tablename__ = "publishers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), unique=True)


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_books_price"),
        CheckConstraint("stock >= 0", name="ck_books_stock"),
        CheckConstraint("rating BETWEEN 0 AND 5", name="ck_books_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article: Mapped[str] = mapped_column(String(20), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id", ondelete="RESTRICT"))
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="RESTRICT"))
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id", ondelete="RESTRICT"))
    rating: Mapped[Decimal] = mapped_column(Numeric(2, 1), default=0)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_ebook: Mapped[bool] = mapped_column(Boolean, default=False)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    publication_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    image: Mapped[str | None] = mapped_column(String(255))

    author: Mapped[Author] = relationship(lazy="joined")
    genre: Mapped[Genre] = relationship(lazy="joined")
    publisher: Mapped[Publisher] = relationship(lazy="joined")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))


class OrderStatus(Base):
    __tablename__ = "order_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("delivery_date >= order_date", name="ck_orders_dates"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_date: Mapped[date] = mapped_column(Date)
    delivery_date: Mapped[date] = mapped_column(Date)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="RESTRICT"))
    status_id: Mapped[int] = mapped_column(ForeignKey("order_statuses.id", ondelete="RESTRICT"))

    client: Mapped[Client] = relationship(lazy="joined")
    status: Mapped[OrderStatus] = relationship(lazy="joined")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", lazy="selectin", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_order_items_qty"),)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="RESTRICT"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates="items")
    book: Mapped[Book] = relationship(lazy="joined")
