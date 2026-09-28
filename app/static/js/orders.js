requireRole(ROLES.MANAGER, ROLES.ADMIN);
renderHeader("orders");

const tbody = document.getElementById("rows");
const errorBox = document.getElementById("error");
let statuses = [];

function rowHtml(o) {
  const options = statuses
    .map((s) => `<option value="${s.id}" ${s.id === o.status_id ? "selected" : ""}>${esc(s.name)}</option>`)
    .join("");
  const items = o.items
    .map((i) => `<li>${esc(i.title)} <span style="opacity:.75">(${esc(i.article)})</span> × ${i.quantity}</li>`)
    .join("");
  return `
    <tr data-id="${o.id}" class="${o.is_overdue ? "overdue" : ""}">
      <td><b>${o.id}</b></td>
      <td>${formatDate(o.order_date)}</td>
      <td>
        <input class="input" type="date" data-field="delivery" value="${o.delivery_date}"
               min="${o.order_date}" aria-label="Дата доставки">
        ${o.is_overdue ? `<div><span class="overdue-tag">Просрочен</span></div>` : ""}
      </td>
      <td>${esc(o.client)}</td>
      <td><select class="input" data-field="status" aria-label="Статус">${options}</select></td>
      <td><ul>${items}</ul></td>
      <td><button class="btn btn-sm" data-save disabled>Сохранить</button></td>
    </tr>`;
}

function render(orders) {
  document.getElementById("counter").textContent =
    `Всего: ${orders.length}, просрочено: ${orders.filter((o) => o.is_overdue).length}`;
  tbody.innerHTML = orders.map(rowHtml).join("");
}

// Кнопка «Сохранить» активна, только если строку изменили.
tbody.addEventListener("input", (event) => {
  const row = event.target.closest("tr");
  if (row) row.querySelector("[data-save]").disabled = false;
});

tbody.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-save]");
  if (!btn) return;
  const row = btn.closest("tr");
  const delivery = row.querySelector('[data-field="delivery"]').value;
  if (!delivery) {
    toast("Укажите дату доставки", true);
    return;
  }
  btn.disabled = true;
  try {
    const updated = await api(`/api/orders/${row.dataset.id}`, {
      method: "PATCH",
      body: {
        status_id: Number(row.querySelector('[data-field="status"]').value),
        delivery_date: delivery,
      },
    });
    await load(false);
    toast(`Заказ №${updated.id} сохранён`);
  } catch (err) {
    btn.disabled = false;
    toast(err.message, true);
  }
});

async function load(withStatuses = true) {
  try {
    if (withStatuses) statuses = await api("/api/order-statuses");
    render(await api("/api/orders"));
    errorBox.hidden = true;
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.hidden = false;
  }
}

load();
