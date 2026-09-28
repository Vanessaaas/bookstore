"""Каталог книг: просмотр, поиск, фильтры, редактирование (администратор)."""
import io
import uuid
from datetime import date, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Author, Book, Genre, OrderItem, Publisher, User
from ..schemas import BookCard, BookDetail, BookIn
from ..security import ROLE_ADMIN, ROLE_MANAGER, ROLE_SELLER, current_user, require_roles

router = APIRouter(prefix="/api/books", tags=["books"])

IMAGES_DIR = Path(__file__).resolve().parents[2] / "resources" / "images"
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_IMAGE_SIDE = 400
NEW_BOOK_DAYS = 30
ILLIQUID_STOCK = 5

staff_only = require_roles(ROLE_SELLER, ROLE_MANAGER, ROLE_ADMIN)
admin_only = require_roles(ROLE_ADMIN)


def _years_ago(today: date, years: int) -> date:
    try:
        return today.replace(year=today.year - years)
    except ValueError:  # 29 февраля
        return today.replace(year=today.year - years, day=28)


def to_card(book: Book, today: date, detail: bool = False) -> BookCard:
    data = dict(
        id=book.id,
        article=book.article,
        title=book.title,
        author=book.author.full_name,
        genre=book.genre.name,
        publisher=book.publisher.name,
        rating=book.rating,
        price=book.price,
        is_ebook=book.is_ebook,
        stock=book.stock,
        publication_date=book.publication_date,
        description=book.description,
        image_url=f"/resources/images/{book.image}" if book.image else None,
        # «Новинка»: издана менее 30 дней назад
        is_new=today - timedelta(days=NEW_BOOK_DAYS) < book.publication_date <= today,
        # «Неликвид»: издана более 2 лет назад и на складе больше 5 штук
        is_illiquid=book.publication_date < _years_ago(today, 2) and book.stock > ILLIQUID_STOCK,
    )
    if detail:
        return BookDetail(**data, genre_id=book.genre_id, publisher_id=book.publisher_id)
    return BookCard(**data)


@router.get("", response_model=list[BookCard])
def list_books(
    search: str | None = Query(None, max_length=100),
    genre_id: int | None = None,
    sort: str | None = Query(None, pattern="^(date_desc|date_asc)$"),
    in_stock: bool = False,
    user: User | None = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = select(Book)
    # Гостю доступен только просмотр: параметры поиска и фильтров игнорируются.
    if user is not None:
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            query = query.where(or_(Book.title.ilike(pattern), Book.description.ilike(pattern)))
        if genre_id:
            query = query.where(Book.genre_id == genre_id)
        if in_stock:
            query = query.where(Book.stock > 0)
        if sort == "date_desc":
            query = query.order_by(Book.publication_date.desc())
        elif sort == "date_asc":
            query = query.order_by(Book.publication_date.asc())
    query = query.order_by(Book.id)
    today = date.today()
    return [to_card(b, today) for b in db.scalars(query).unique()]


@router.get("/{book_id}", response_model=BookDetail)
def get_book(book_id: int, _: User = Depends(staff_only), db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(404, "Книга не найдена")
    return to_card(book, date.today(), detail=True)


def _parse_form(**fields) -> BookIn:
    try:
        return BookIn(**fields)
    except ValidationError as exc:
        messages = []
        for err in exc.errors():
            field = err["loc"][0] if err["loc"] else ""
            messages.append(f"{FIELD_NAMES.get(field, field)}: {_ru_error(err)}")
        raise HTTPException(422, "; ".join(messages)) from None


def _ru_error(err: dict) -> str:
    ctx = err.get("ctx", {})
    kind = err["type"]
    if kind == "greater_than_equal":
        return "не может быть отрицательным" if ctx.get("ge") == 0 else f"не меньше {ctx.get('ge')}"
    if kind == "less_than_equal":
        return f"не больше {ctx.get('le')}"
    if kind in ("string_too_short", "missing"):
        return "обязательное поле"
    if kind == "string_too_long":
        return f"не длиннее {ctx.get('max_length')} символов"
    if kind in ("decimal_max_places", "decimal_max_digits"):
        return "слишком много знаков после запятой"
    if kind.startswith(("int_", "decimal_", "float_")):
        return "введите число"
    if kind.startswith("date_"):
        return "неверная дата"
    if kind == "value_error":
        return str(ctx.get("error", err["msg"]))
    return err["msg"]


FIELD_NAMES = {
    "article": "Артикул", "title": "Название", "author": "Автор", "genre_id": "Жанр",
    "publisher_id": "Издатель", "rating": "Рейтинг", "price": "Стоимость",
    "is_ebook": "Электронная книга", "stock": "Количество",
    "publication_date": "Дата издания", "description": "Описание",
}


def _save_image(upload: UploadFile) -> str:
    """Проверяет размер файла, уменьшает до 400×400 и копирует в resources/images."""
    raw = upload.file.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(422, "Размер изображения не должен превышать 2 МБ")
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(422, "Файл не является изображением") from None
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.jpg"
    img.save(IMAGES_DIR / name, "JPEG", quality=85)
    return name


def _delete_image(name: str | None, db: Session) -> None:
    if not name:
        return
    still_used = db.scalar(select(exists().where(Book.image == name)))
    if not still_used:
        (IMAGES_DIR / name).unlink(missing_ok=True)


def _apply(book: Book, data: BookIn, db: Session) -> None:
    if db.get(Genre, data.genre_id) is None:
        raise HTTPException(422, "Выбранный жанр не существует")
    if db.get(Publisher, data.publisher_id) is None:
        raise HTTPException(422, "Выбранный издатель не существует")
    duplicate = db.scalar(select(Book.id).where(Book.article == data.article, Book.id != book.id))
    if duplicate:
        raise HTTPException(409, f"Книга с артикулом {data.article} уже есть в каталоге")
    author = db.scalar(select(Author).where(Author.full_name == data.author))
    if author is None:
        author = Author(full_name=data.author)
        db.add(author)
        db.flush()
    book.article = data.article
    book.title = data.title
    book.author_id = author.id
    book.genre_id = data.genre_id
    book.publisher_id = data.publisher_id
    book.rating = data.rating
    book.price = data.price
    book.is_ebook = data.is_ebook
    book.stock = data.stock
    book.publication_date = data.publication_date
    book.description = (data.description or "").strip() or None


def _form_fields(
    article: str = Form(...), title: str = Form(...), author: str = Form(...),
    genre_id: int = Form(...), publisher_id: int = Form(...), rating: str = Form("0"),
    price: str = Form(...), is_ebook: bool = Form(False), stock: str = Form(...),
    publication_date: str = Form(...), description: str | None = Form(None),
) -> dict:
    return dict(
        article=article, title=title, author=author, genre_id=genre_id,
        publisher_id=publisher_id, rating=rating, price=price, is_ebook=is_ebook,
        stock=stock, publication_date=publication_date, description=description,
    )


@router.post("", response_model=BookDetail, status_code=201)
def create_book(
    fields: dict = Depends(_form_fields),
    image: UploadFile | None = File(None),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    data = _parse_form(**fields)
    book = Book()  # id назначает СУБД
    _apply(book, data, db)
    if image is not None and image.filename:
        book.image = _save_image(image)
    db.add(book)
    db.commit()
    db.refresh(book)
    return to_card(book, date.today(), detail=True)


@router.put("/{book_id}", response_model=BookDetail)
def update_book(
    book_id: int,
    fields: dict = Depends(_form_fields),
    image: UploadFile | None = File(None),
    remove_image: bool = Form(False),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(404, "Книга не найдена")
    data = _parse_form(**fields)
    _apply(book, data, db)
    old_image = book.image
    if image is not None and image.filename:
        book.image = _save_image(image)
    elif remove_image:
        book.image = None
    db.commit()
    if old_image != book.image:
        _delete_image(old_image, db)
    db.refresh(book)
    return to_card(book, date.today(), detail=True)


@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(404, "Книга не найдена")
    in_orders = db.scalar(select(exists().where(OrderItem.book_id == book_id)))
    if in_orders:
        raise HTTPException(409, "Книгу нельзя удалить: она присутствует в заказах")
    image = book.image
    db.delete(book)
    db.commit()
    _delete_image(image, db)
