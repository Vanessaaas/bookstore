requireRole(ROLES.ADMIN);
renderHeader("catalog");

const MAX_IMAGE_BYTES = 2 * 1024 * 1024;
const bookId = new URLSearchParams(location.search).get("id");
const form = document.getElementById("book-form");
const errorBox = document.getElementById("error");
const preview = document.getElementById("preview");
const fileInput = document.getElementById("image");
const clearBtn = document.getElementById("clear-image");
const deleteBtn = document.getElementById("delete");

let removeImage = false;

function setPreview(src) {
  preview.src = src || PLACEHOLDER;
  preview.className = src ? "" : "placeholder";
  clearBtn.hidden = !src;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
  errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
}

function fillOptions(select, items) {
  select.innerHTML = `<option value="">— выберите —</option>` +
    items.map((i) => `<option value="${i.id}">${esc(i.name)}</option>`).join("");
}

document.getElementById("pick-image").addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;
  if (file.size > MAX_IMAGE_BYTES) {
    fileInput.value = "";
    showError("Размер изображения не должен превышать 2 МБ");
    return;
  }
  errorBox.hidden = true;
  removeImage = false;
  setPreview(URL.createObjectURL(file));
});

clearBtn.addEventListener("click", () => {
  fileInput.value = "";
  removeImage = true;
  setPreview(null);
});

function validate() {
  const errors = [];
  for (const [name, label] of [["article", "Артикул"], ["title", "Название"], ["author", "Автор"],
    ["genre_id", "Жанр"], ["publisher_id", "Издатель"], ["publication_date", "Дата издания"],
    ["price", "Стоимость"], ["stock", "Количество"]]) {
    if (!String(form[name].value).trim()) errors.push(`Заполните поле «${label}»`);
  }
  const price = Number(form.price.value);
  const stock = Number(form.stock.value);
  const rating = Number(form.rating.value || 0);
  if (form.price.value !== "" && (Number.isNaN(price) || price < 0)) errors.push("Стоимость не может быть отрицательной");
  if (form.stock.value !== "" && (!Number.isInteger(stock) || stock < 0)) errors.push("Количество должно быть целым неотрицательным числом");
  if (Number.isNaN(rating) || rating < 0 || rating > 5) errors.push("Рейтинг должен быть от 0 до 5");
  return errors;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  const errors = validate();
  if (errors.length) {
    showError(errors.join(". "));
    return;
  }
  const data = new FormData();
  for (const name of ["article", "title", "author", "genre_id", "publisher_id", "rating",
    "price", "stock", "publication_date", "description"]) {
    data.append(name, form[name].value.trim());
  }
  data.set("rating", form.rating.value || "0");
  data.append("is_ebook", form.is_ebook.checked ? "true" : "false");
  if (fileInput.files[0]) data.append("image", fileInput.files[0]);
  if (bookId && removeImage) data.append("remove_image", "true");

  const saveBtn = document.getElementById("save");
  saveBtn.disabled = true;
  try {
    await api(bookId ? `/api/books/${bookId}` : "/api/books", { method: bookId ? "PUT" : "POST", body: data });
    location.href = "/static/catalog.html";
  } catch (err) {
    showError(err.message);
  } finally {
    saveBtn.disabled = false;
  }
});

deleteBtn.addEventListener("click", async () => {
  if (!confirm(`Удалить книгу «${form.title.value}»? Действие нельзя отменить.`)) return;
  try {
    await api(`/api/books/${bookId}`, { method: "DELETE" });
    location.href = "/static/catalog.html";
  } catch (err) {
    showError(err.message);
  }
});

async function init() {
  const [genres, publishers, authors] = await Promise.all([
    api("/api/genres"), api("/api/publishers"), api("/api/authors"),
  ]);
  fillOptions(form.genre_id, genres);
  fillOptions(form.publisher_id, publishers);
  document.getElementById("authors-list").innerHTML =
    authors.map((a) => `<option value="${esc(a.name)}">`).join("");

  if (!bookId) return;
  document.getElementById("form-title").textContent = "Редактирование книги";
  deleteBtn.hidden = false;
  const b = await api(`/api/books/${bookId}`);
  form.article.value = b.article;
  form.title.value = b.title;
  form.author.value = b.author;
  form.genre_id.value = b.genre_id;
  form.publisher_id.value = b.publisher_id;
  form.rating.value = b.rating;
  form.price.value = b.price;
  form.stock.value = b.stock;
  form.publication_date.value = b.publication_date;
  form.description.value = b.description ?? "";
  form.is_ebook.checked = b.is_ebook;
  setPreview(b.image_url);
}

init().catch((err) => showError(err.message));
