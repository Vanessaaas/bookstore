const form = document.getElementById("login-form");
const errorBox = document.getElementById("error");
const submitBtn = document.getElementById("submit");

Session.clear();

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  const login = form.login.value.trim();
  const password = form.password.value;
  if (!login || !password) {
    showError("Введите логин и пароль");
    return;
  }
  submitBtn.disabled = true;
  try {
    const data = await api("/api/auth/login", { method: "POST", body: { login, password } });
    Session.set(data);
    location.href = "/static/catalog.html";
  } catch (err) {
    showError(err.message);
    form.password.value = "";
    form.password.focus();
  } finally {
    submitBtn.disabled = false;
  }
});

document.getElementById("guest").addEventListener("click", () => {
  Session.set({ token: null, user: { full_name: "Гость", role: ROLES.GUEST } });
  location.href = "/static/catalog.html";
});
