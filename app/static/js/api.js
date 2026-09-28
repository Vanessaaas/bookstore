// Общие функции: сессия, запросы к API, шапка страницы.
const ROLES = {
  ADMIN: "Администратор",
  MANAGER: "Менеджер",
  SELLER: "Продавец",
  GUEST: "Гость",
};

const PLACEHOLDER = "/static/img/picture.png";

const Session = {
  get() {
    const raw = sessionStorage.getItem("bookstore.session");
    return raw ? JSON.parse(raw) : null;
  },
  set(data) {
    sessionStorage.setItem("bookstore.session", JSON.stringify(data));
  },
  clear() {
    sessionStorage.removeItem("bookstore.session");
  },
  role() {
    return this.get()?.user.role ?? null;
  },
};

async function api(path, { method = "GET", body, signal } = {}) {
  const headers = {};
  const session = Session.get();
  if (session?.token) headers.Authorization = `Bearer ${session.token}`;
  let payload = body;
  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const res = await fetch(path, { method, headers, body: payload, signal });
  if (res.status === 401 && session?.token) {
    Session.clear();
    location.href = "/static/index.html";
    throw new Error("Сессия истекла");
  }
  if (!res.ok) {
    let message = `Ошибка ${res.status}`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail)) message = data.detail.map((d) => d.msg).join("; ");
    } catch { /* ответ без JSON */ }
    throw new Error(message);
  }
  return res.status === 204 ? null : res.json();
}

// Пускает на страницу только перечисленные роли, иначе отправляет на вход.
function requireRole(...roles) {
  const role = Session.role();
  if (!role || !roles.includes(role)) {
    location.replace(role ? "/static/catalog.html" : "/static/index.html");
    throw new Error("Нет доступа");
  }
  return Session.get().user;
}

function renderHeader(active) {
  const user = Session.get().user;
  document.title = `BookStore — ${user.full_name}`;
  const canOrders = [ROLES.MANAGER, ROLES.ADMIN].includes(user.role);
  const header = document.createElement("header");
  header.className = "topbar";
  header.innerHTML = `
    <div class="topbar-inner">
      <a class="brand" href="/static/catalog.html"><img src="/static/img/Icon.png" alt=""><span>BookStore</span></a>
      <nav class="nav">
        <a href="/static/catalog.html" class="${active === "catalog" ? "active" : ""}">Каталог</a>
        ${canOrders ? `<a href="/static/orders.html" class="${active === "orders" ? "active" : ""}">Заказы</a>` : ""}
      </nav>
      <div class="user">
        <div>
          <div class="user-name"></div>
          <div class="user-role"></div>
        </div>
        <button class="btn btn-outline btn-sm" id="logout">Выйти</button>
      </div>
    </div>`;
  header.querySelector(".user-name").textContent = user.full_name;
  header.querySelector(".user-role").textContent =
    user.role === ROLES.GUEST ? "Только просмотр каталога" : user.role;
  header.querySelector("#logout").addEventListener("click", () => {
    Session.clear();
    location.href = "/static/index.html";
  });
  document.body.prepend(header);
}

function toast(message, isError = false) {
  const el = document.createElement("div");
  el.className = "toast" + (isError ? " error" : "");
  el.textContent = message;
  document.body.append(el);
  setTimeout(() => el.remove(), 3500);
}

function esc(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function formatDate(iso) {
  const [y, m, d] = iso.split("-");
  return `${d}.${m}.${y}`;
}

function formatPrice(value) {
  return Number(value).toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + " ₽";
}
