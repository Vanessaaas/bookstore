"""Рисует ER-диаграмму БД BookStore в docs/er_diagram.pdf (нотация «вороньи лапки»).

Запуск: python tools/draw_er.py
"""
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "er_diagram.pdf"

pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", "C:/Windows/Fonts/ariali.ttf"))

W, H = landscape(A3)
BOX_W = 240
HEAD_H = 24
ROW_H = 17

BRAND = HexColor("#1f6fbf")
LINE = HexColor("#34495e")
GRID = HexColor("#c9d6e3")
KEY_BG = HexColor("#eaf2fb")

# (ключ, подпись, тип, имя поля)
TABLES = {
    "authors": ("Авторы", 50, 700, [
        ("PK", "id", "INTEGER"),
        ("UQ", "full_name", "VARCHAR(150)"),
    ]),
    "genres": ("Жанры", 50, 590, [
        ("PK", "id", "INTEGER"),
        ("UQ", "name", "VARCHAR(100)"),
    ]),
    "publishers": ("Издатели", 50, 480, [
        ("PK", "id", "INTEGER"),
        ("UQ", "name", "VARCHAR(100)"),
    ]),
    "books": ("Книги", 350, 740, [
        ("PK", "id", "INTEGER"),
        ("UQ", "article", "VARCHAR(20)"),
        ("", "title", "VARCHAR(200)"),
        ("FK", "author_id", "INTEGER"),
        ("FK", "genre_id", "INTEGER"),
        ("FK", "publisher_id", "INTEGER"),
        ("", "rating", "NUMERIC(2,1)"),
        ("", "price", "NUMERIC(10,2) ≥ 0"),
        ("", "is_ebook", "BOOLEAN"),
        ("", "stock", "INTEGER ≥ 0"),
        ("", "publication_date", "DATE"),
        ("", "description", "TEXT NULL"),
        ("", "image", "VARCHAR(255) NULL"),
    ]),
    "order_items": ("Состав заказа", 630, 740, [
        ("PK FK", "order_id", "INTEGER"),
        ("PK FK", "book_id", "INTEGER"),
        ("", "quantity", "INTEGER > 0"),
    ]),
    "orders": ("Заказы", 930, 740, [
        ("PK", "id", "INTEGER"),
        ("", "order_date", "DATE"),
        ("", "delivery_date", "DATE"),
        ("FK", "client_id", "INTEGER"),
        ("FK", "status_id", "INTEGER"),
    ]),
    "clients": ("Клиенты", 630, 560, [
        ("PK", "id", "INTEGER"),
        ("", "full_name", "VARCHAR(150)"),
    ]),
    "order_statuses": ("Статусы заказа", 630, 450, [
        ("PK", "id", "INTEGER"),
        ("UQ", "name", "VARCHAR(50)"),
        ("", "is_final", "BOOLEAN"),
    ]),
    "roles": ("Роли", 50, 300, [
        ("PK", "id", "INTEGER"),
        ("UQ", "name", "VARCHAR(50)"),
    ]),
    "users": ("Пользователи", 350, 330, [
        ("PK", "id", "INTEGER"),
        ("", "full_name", "VARCHAR(150)"),
        ("UQ", "login", "VARCHAR(50)"),
        ("", "password_hash", "VARCHAR(200)"),
        ("FK", "role_id", "INTEGER"),
    ]),
}

# (таблица «многие», поле FK, таблица «один», поле PK, x вертикального участка)
RELATIONS = [
    ("books", "author_id", "authors", "id", 310),
    ("books", "genre_id", "genres", "id", 318),
    ("books", "publisher_id", "publishers", "id", 326),
    ("order_items", "book_id", "books", "id", 608),
    ("order_items", "order_id", "orders", "id", 900),
    ("orders", "client_id", "clients", "id", 900),
    ("orders", "status_id", "order_statuses", "id", 890),
    ("users", "role_id", "roles", "id", 318),
]


def row_y(table: str, field: str) -> float:
    _, _, top, fields = TABLES[table]
    idx = [f[1] for f in fields].index(field)
    return top - HEAD_H - ROW_H * idx - ROW_H / 2


def draw_table(c: canvas.Canvas, key: str) -> None:
    title, x, top, fields = TABLES[key]
    height = HEAD_H + ROW_H * len(fields)
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.setFillColor(white)
    c.rect(x, top - height, BOX_W, height, fill=1)
    c.setFillColor(BRAND)
    c.rect(x, top - HEAD_H, BOX_W, HEAD_H, fill=1)
    c.setFillColor(white)
    c.setFont("Arial-Bold", 11)
    c.drawString(x + 8, top - 16, key)
    c.setFont("Arial", 9)
    c.drawRightString(x + BOX_W - 8, top - 16, title)
    for i, (mark, name, typ) in enumerate(fields):
        y = top - HEAD_H - ROW_H * (i + 1)
        if "PK" in mark:
            c.setFillColor(KEY_BG)
            c.rect(x, y, BOX_W, ROW_H, fill=1, stroke=0)
        c.setStrokeColor(GRID)
        c.line(x, y + ROW_H, x + BOX_W, y + ROW_H)
        c.setFillColor(LINE)
        c.setFont("Arial-Bold", 7.5)
        c.drawString(x + 6, y + 5, mark)
        font = "Arial-Bold" if "PK" in mark else "Arial-Italic" if "FK" in mark else "Arial"
        c.setFont(font, 9.5)
        c.drawString(x + 44, y + 5, name)
        c.setFont("Arial", 8.5)
        c.setFillColor(HexColor("#5d6b7a"))
        c.drawRightString(x + BOX_W - 8, y + 5, typ)
    c.setStrokeColor(LINE)
    c.rect(x, top - height, BOX_W, height, fill=0)


def crow_foot(c, x, y, direction):
    """Сторона «многие»: три линии, сходящиеся к сущности, плюс кружок/черта."""
    d = direction  # +1: сущность справа от точки, -1: слева
    tip = x - d * 12
    c.line(tip, y, x, y + 6)
    c.line(tip, y, x, y)
    c.line(tip, y, x, y - 6)
    c.line(x - d * 16, y - 6, x - d * 16, y + 6)


def one_mark(c, x, y, direction):
    """Сторона «один (обязательно)»: две вертикальные черты."""
    d = direction
    c.line(x - d * 7, y - 6, x - d * 7, y + 6)
    c.line(x - d * 12, y - 6, x - d * 12, y + 6)


def draw_relation(c, many, fk, one, pk, mid_x):
    _, mx, _, _ = TABLES[many]
    _, ox, _, _ = TABLES[one]
    y1, y2 = row_y(many, fk), row_y(one, pk)
    if ox > mx:  # «один» правее
        x1, x2 = mx + BOX_W, ox
        d1, d2 = -1, 1
    else:
        x1, x2 = mx, ox + BOX_W
        d1, d2 = 1, -1
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    path = c.beginPath()
    path.moveTo(x1, y1)
    path.lineTo(mid_x, y1)
    path.lineTo(mid_x, y2)
    path.lineTo(x2, y2)
    c.drawPath(path, stroke=1, fill=0)
    crow_foot(c, x1, y1, d1)
    one_mark(c, x2, y2, d2)


def legend(c):
    x, y = 630, 330
    c.setFillColor(LINE)
    c.setFont("Arial-Bold", 11)
    c.drawString(x, y, "Обозначения")
    c.setFont("Arial", 9.5)
    c.setStrokeColor(LINE)
    rows = [
        ("one", "ровно один (обязательная связь)"),
        ("many", "один или много"),
    ]
    for i, (kind, text) in enumerate(rows):
        yy = y - 22 - i * 22
        c.line(x, yy, x + 50, yy)
        if kind == "one":
            one_mark(c, x + 50, yy, 1)
        else:
            crow_foot(c, x + 50, yy, 1)
        c.drawString(x + 62, yy - 3, text)
    notes = [
        "PK: первичный ключ, FK: внешний ключ, UQ: уникальное поле",
        "Все таблицы находятся в 3НФ: справочники вынесены,",
        "составной ключ (order_id, book_id) в order_items.",
        "Удаление книги из заказа запрещено: FK ON DELETE RESTRICT.",
    ]
    for i, text in enumerate(notes):
        c.drawString(x, y - 80 - i * 15, text)


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H))
    c.setTitle("BookStore: ER-диаграмма")
    c.setFillColor(LINE)
    c.setFont("Arial-Bold", 18)
    c.drawString(50, H - 45, "ER-диаграмма базы данных «BookStore»")
    c.setFont("Arial", 10)
    c.drawString(50, H - 62, "СУБД PostgreSQL · нотация «вороньи лапки» (Crow's Foot)")
    for many, fk, one, pk, mid_x in RELATIONS:
        draw_relation(c, many, fk, one, pk, mid_x)
    for key in TABLES:
        draw_table(c, key)
    legend(c)
    c.showPage()
    c.save()
    print(f"Готово: {OUT}")


if __name__ == "__main__":
    main()
