"""Точка входа: uvicorn app.main:app --reload"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .routers import auth, books, orders, references

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="BookStore")

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(orders.router)
app.include_router(references.router)

(BASE_DIR / "resources" / "images").mkdir(parents=True, exist_ok=True)
app.mount("/resources", StaticFiles(directory=BASE_DIR / "resources"), name="resources")
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")


@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse("/static/index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return RedirectResponse("/static/favicon.ico")
