"""Блок-схема алгоритма авторизации по ГОСТ 19.701-90 → docs/login_flowchart.pdf.

Размеры символов: a = 20 мм, b = 1,5a = 30 мм. Основное направление потока:
сверху вниз и слева направо, линии против этого направления имеют стрелки.
Запуск: python tools/draw_flowchart.py
"""
from pathlib import Path

from reportlab.lib.colors import black, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "login_flowchart.pdf"

pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"))

W, H = A4
A = 20 * mm          # высота символа
B = 1.5 * A          # ширина символа
STEP = A + 7 * mm    # шаг по вертикали
FONT = 7.5
CX = W / 2           # основная колонка
LX = CX - 52 * mm    # колонка сообщений об ошибках
RX = CX + 52 * mm    # колонка гостевого входа
LOOP_X = LX - B / 2 - 8 * mm


def wrap(text: str, width: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        probe = f"{cur} {word}".strip()
        if stringWidth(probe, "Arial", FONT) <= width:
            cur = probe
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def label(c, x, y, text, width=B - 10):
    lines = wrap(text, width)
    lh = FONT + 1.5
    top = y + (len(lines) - 1) * lh / 2 - FONT / 3
    c.setFillColor(black)
    c.setFont("Arial", FONT)
    for i, line in enumerate(lines):
        c.drawCentredString(x, top - i * lh, line)
    c.setFillColor(white)


def terminator(c, x, y, text):
    h = A / 2  # ГОСТ: терминатор высотой 0,5a
    c.roundRect(x - B / 2, y - h / 2, B, h, h / 2, stroke=1, fill=1)
    label(c, x, y, text)
    return h / 2


def process(c, x, y, text):
    c.rect(x - B / 2, y - A / 2, B, A, stroke=1, fill=1)
    label(c, x, y, text)
    return A / 2


def data(c, x, y, text):
    k = A * 0.25
    p = c.beginPath()
    p.moveTo(x - B / 2 + k, y + A / 2)
    p.lineTo(x + B / 2, y + A / 2)
    p.lineTo(x + B / 2 - k, y - A / 2)
    p.lineTo(x - B / 2, y - A / 2)
    p.close()
    c.drawPath(p, stroke=1, fill=1)
    label(c, x, y, text, B - 2 * k - 4)
    return A / 2


def decision(c, x, y, text):
    p = c.beginPath()
    p.moveTo(x, y + A / 2)
    p.lineTo(x + B / 2, y)
    p.lineTo(x, y - A / 2)
    p.lineTo(x - B / 2, y)
    p.close()
    c.drawPath(p, stroke=1, fill=1)
    label(c, x, y, text, B * 0.55)
    return A / 2


def comment(c, x_from, y, x, text, width=28 * mm):
    """Символ «Комментарий»: пунктирная связь и открытая скобка."""
    c.setDash(2, 2)
    c.line(x_from, y, x, y)
    c.setDash()
    c.line(x, y + A / 2, x, y - A / 2)
    c.line(x, y + A / 2, x + 4 * mm, y + A / 2)
    c.line(x, y - A / 2, x + 4 * mm, y - A / 2)
    c.setFillColor(black)
    c.setFont("Arial", FONT)
    for i, line in enumerate(wrap(text, width)):
        c.drawString(x + 2 * mm, y + 6 - i * (FONT + 1.5), line)
    c.setFillColor(white)


def arrow(c, x, y, direction):
    s = 4
    p = c.beginPath()
    if direction == "right":
        p.moveTo(x, y); p.lineTo(x - s * 1.6, y + s / 2); p.lineTo(x - s * 1.6, y - s / 2)
    elif direction == "left":
        p.moveTo(x, y); p.lineTo(x + s * 1.6, y + s / 2); p.lineTo(x + s * 1.6, y - s / 2)
    elif direction == "up":
        p.moveTo(x, y); p.lineTo(x - s / 2, y - s * 1.6); p.lineTo(x + s / 2, y - s * 1.6)
    p.close()
    c.setFillColor(black)
    c.drawPath(p, stroke=0, fill=1)
    c.setFillColor(white)


def polyline(c, *points):
    p = c.beginPath()
    p.moveTo(*points[0])
    for pt in points[1:]:
        p.lineTo(*pt)
    c.drawPath(p, stroke=1, fill=0)


def text_at(c, x, y, text, bold=False, size=FONT):
    c.setFillColor(black)
    c.setFont("Arial-Bold" if bold else "Arial", size)
    c.drawString(x, y, text)
    c.setFillColor(white)


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("BookStore: блок-схема авторизации")
    c.setLineWidth(0.8)

    # Рамка листа (поля по ГОСТ 2.301: слева 20 мм, остальные 5 мм)
    c.rect(20 * mm, 5 * mm, W - 25 * mm, H - 10 * mm)
    c.setFillColor(black)
    c.setFont("Arial-Bold", 12)
    c.drawCentredString(CX, H - 17 * mm, "Блок-схема алгоритма авторизации пользователя")
    c.setFont("Arial", 9)
    c.drawCentredString(CX, H - 22 * mm, "ИС «BookStore» · ГОСТ 19.701-90")
    c.setFillColor(white)
    c.setStrokeColor(black)

    y = [H - 34 * mm - i * STEP for i in range(10)]
    y[0] += 3 * mm  # терминатор ниже остальных символов

    # Основная ветвь
    terminator(c, CX, y[0], "Начало")
    data(c, CX, y[1], "Вывод окна авторизации")
    decision(c, CX, y[2], "Вход в режиме гостя?")
    data(c, CX, y[3], "Ввод логина и пароля")
    decision(c, CX, y[4], "Логин и пароль заполнены?")
    process(c, CX, y[5], "Поиск пользователя в БД по логину, проверка хэша пароля")
    decision(c, CX, y[6], "Пользователь найден, пароль верен?")
    process(c, CX, y[7], "Получение ФИО и роли, выдача токена сессии")
    process(c, CX, y[8], "Настройка интерфейса по роли, вывод ФИО в заголовок окна")
    terminator(c, CX, y[9], "Конец")

    # Вертикальные линии основной ветви (сверху вниз, без стрелок)
    c.line(CX, y[0] - A / 4, CX, y[1] + A / 2)
    for i in range(1, 8):
        c.line(CX, y[i] - A / 2, CX, y[i + 1] + A / 2)
    c.line(CX, y[8] - A / 2, CX, y[9] + A / 4)

    # Подписи выходов решений
    text_at(c, CX + 2, y[2] - A / 2 - 8, "Нет")
    text_at(c, CX + B / 2 + 2, y[2] + 3, "Да")
    text_at(c, CX + 2, y[4] - A / 2 - 8, "Да")
    text_at(c, CX - B / 2 - 14, y[4] + 3, "Нет")
    text_at(c, CX + 2, y[6] - A / 2 - 8, "Да")
    text_at(c, CX - B / 2 - 14, y[6] + 3, "Нет")

    # Гостевой вход: вправо, вниз и обратно к настройке интерфейса
    process(c, RX, y[4], "Роль := «Гость», доступен только просмотр каталога")
    polyline(c, (CX + B / 2, y[2]), (RX, y[2]), (RX, y[4] + A / 2))
    polyline(c, (RX, y[4] - A / 2), (RX, y[8]), (CX + B / 2, y[8]))
    arrow(c, CX + B / 2, y[8], "left")

    # Ошибки ввода: сообщение и возврат к вводу
    data(c, LX, y[4] - STEP / 2, "Сообщение «Введите логин и пароль»")
    polyline(c, (CX - B / 2, y[4]), (LX, y[4]), (LX, y[4] - STEP / 2 + A / 2))
    data(c, LX, y[6] - STEP / 2, "Сообщение «Неверный логин или пароль»")
    polyline(c, (CX - B / 2, y[6]), (LX, y[6]), (LX, y[6] - STEP / 2 + A / 2))

    polyline(c, (LX - B / 2 + A / 8, y[6] - STEP / 2), (LOOP_X, y[6] - STEP / 2), (LOOP_X, y[3]),
             (CX - B / 2 + A * 0.125, y[3]))
    c.line(LX - B / 2 + A / 8, y[4] - STEP / 2, LOOP_X, y[4] - STEP / 2)
    arrow(c, LOOP_X, y[4] + 4 * mm, "up")
    arrow(c, CX - B / 2 + A * 0.125, y[3], "right")

    # Комментарии
    comment(c, CX + B / 2 - A * 0.125, y[3], CX + B / 2 + 6 * mm,
            "Символы пароля скрыты (поле type=password)")
    comment(c, CX + B / 2, y[5], CX + B / 2 + 6 * mm,
            "Таблицы users и roles")

    c.showPage()
    c.save()
    print(f"Готово: {OUT}")


if __name__ == "__main__":
    main()
