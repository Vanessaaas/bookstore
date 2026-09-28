const user = requireRole(ROLES.GUEST, ROLES.SELLER, ROLES.MANAGER, ROLES.ADMIN);
renderHeader("catalog");

const isGuest = user.role === ROLES.GUEST;
const isAdmin = user.role === ROLES.ADMIN;

const grid = document.getElementById("grid");
const empty = document.getElementById("empty");
const counter = document.getElementById("counter");
const errorBox = document.getElementById("error");
const controls = {
  search: document.getElementById("search"),
  genre: document.getElementById("genre"),
  sort: document.getElementById("sort"),
  inStock: document.getElementById("in-stock"),
};

document.getElementById("legend").hidden = false;
document.getElementById("toolbar").hidden = isGuest;
document.getElementById("add-book").hidden = !isAdmin;

let pending = null;

async function loadBooks() {
  const params = new URLSearchParams();
  if (!isGuest) {
    const search = controls.search.value.trim();
    if (search) params.set("search", search);
    if (controls.genre.value) params.set("genre_id", controls.genre.value);
    if (controls.sort.value) params.set("sort", controls.sort.value);
    if (controls.inStock.checked) params.set("in_stock", "true");
  }
  // Отменяем предыдущий запрос, чтобы устаревший ответ не перезаписал новый.
  pending?.abort();
  pending = new AbortController();
  try {
    const books = await api(`/api/books?${params}`, { signal: pending.signal });
    errorBox.hidden = true;
    render(books);
  } catch (err) {
    if (err.name === "AbortError") return;
    errorBox.textContent = err.message;
    errorBox.hidden = false;
  }
}

function render(books) {
  counter.textContent = `Найдено: ${books.length}`;
  empty.hidden = books.length > 0;
  grid.innerHTML = books.map(cardHtml).join("");
}

function cardHtml(b) {
  const cover = b.image_url
    ? `<img src="${esc(b.image_url)}" alt="${esc(b.title)}" onerror="this.onerror=null;this.src='${PLACEHOLDER}';this.className='placeholder'">`
    : `<img class="placeholder" src="${PLACEHOLDER}" alt="Нет обложки">`;
  const badges = [
    b.is_ebook ? `<span class="badge badge-ebook">E-book</span>` : "",
    b.is_new ? `<span class="badge badge-new">Новинка</span>` : "",
    b.is_illiquid ? `<span class="badge badge-illiquid">Неликвид</span>` : "",
    !b.is_ebook && b.stock === 0 ? `<span class="badge badge-out">Нет в наличии</span>` : "",
  ].join("");
  const actions = isAdmin
    ? `<div class="card-actions">
         <a class="btn btn-outline btn-sm" href="/static/book-form.html?id=${b.id}">Изменить</a>
         <button class="btn btn-danger btn-sm" data-delete="${b.id}" data-title="${esc(b.title)}">Удалить</button>
       </div>`
    : "";
  return `
    <article class="card${b.is_illiquid ? " illiquid" : ""}">
      <div class="card-cover">${cover}</div>
      <div class="badges">${badges}</div>
      <div class="card-body">
        <h3 class="card-title${b.is_new ? " is-new" : ""}">${esc(b.title)}</h3>
        <div class="card-meta"><span>${esc(b.author)}</span></div>
        <div class="card-meta"><span>Жанр: ${esc(b.genre)}</span><span class="rating">★ ${Number(b.rating).toFixed(1)}</span></div>
        <div class="card-meta"><span>Издана: ${formatDate(b.publication_date)}</span><span>${b.is_ebook ? "" : `На складе: ${b.stock}`}</span></div>
        <div class="card-price">${formatPrice(b.price)}</div>
      </div>
      ${actions}
    </article>`;
}

grid.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-delete]");
  if (!btn) return;
  if (!confirm(`Удалить книгу «${btn.dataset.title}»? Действие нельзя отменить.`)) return;
  try {
    await api(`/api/books/${btn.dataset.delete}`, { method: "DELETE" });
    toast("Книга удалена");
    loadBooks();
  } catch (err) {
    alert(err.message);
  }
});

let debounce;
controls.search.addEventListener("input", () => {
  clearTimeout(debounce);
  debounce = setTimeout(loadBooks, 200);
});
[controls.genre, controls.sort, controls.inStock].forEach((el) => el.addEventListener("change", loadBooks));

async function init() {
  if (!isGuest) {
    const genres = await api("/api/genres");
    controls.genre.insertAdjacentHTML(
      "beforeend",
      genres.map((g) => `<option value="${g.id}">${esc(g.name)}</option>`).join(""),
    );
  }
  loadBooks();
}

init().catch((err) => toast(err.message, true));
