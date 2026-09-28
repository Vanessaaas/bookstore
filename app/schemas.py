"""Pydantic-схемы запросов и ответов."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class LoginIn(BaseModel):
    login: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=100)


class UserOut(BaseModel):
    full_name: str
    role: str


class LoginOut(BaseModel):
    token: str
    user: UserOut


class RefItem(BaseModel):
    id: int
    name: str


class BookCard(BaseModel):
    id: int
    article: str
    title: str
    author: str
    genre: str
    publisher: str
    rating: Decimal
    price: Decimal
    is_ebook: bool
    stock: int
    publication_date: date
    description: str | None
    image_url: str | None
    is_new: bool
    is_illiquid: bool


class BookDetail(BookCard):
    genre_id: int
    publisher_id: int


class BookIn(BaseModel):
    """Проверка полей формы книги. Отрицательные цена и количество отклоняются."""

    article: str = Field(min_length=1, max_length=20)
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=150)
    genre_id: int
    publisher_id: int
    rating: Decimal = Field(ge=0, le=5, max_digits=2, decimal_places=1)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    is_ebook: bool
    stock: int = Field(ge=0)
    publication_date: date
    description: str | None = None

    @field_validator("article", "title", "author")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Поле не может быть пустым")
        return value


class OrderItemOut(BaseModel):
    article: str
    title: str
    quantity: int


class OrderOut(BaseModel):
    id: int
    order_date: date
    delivery_date: date
    client: str
    status_id: int
    status: str
    is_overdue: bool
    items: list[OrderItemOut]


class OrderUpdate(BaseModel):
    status_id: int
    delivery_date: date
