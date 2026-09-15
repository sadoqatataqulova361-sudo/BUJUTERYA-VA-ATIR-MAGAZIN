// ---------- Telegram WebApp bilan ishga tushirish ----------
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
}

const tgUser = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) ? tg.initDataUnsafe.user : null;
const USER_ID = tgUser ? tgUser.id : 0;

// ---------- Holat (state) ----------
let CATEGORIES = [];
let PRODUCTS = [];
let CART = JSON.parse(localStorage.getItem("cart") || "{}"); // { product_id: qty }
let CURRENT_CATEGORY = null;
let CURRENT_PRODUCT_ID = null;

function saveCart() {
  localStorage.setItem("cart", JSON.stringify(CART));
  updateCartBadge();
}

function formatPrice(v) {
  return Math.round(v).toLocaleString("ru-RU").replace(/,/g, " ") + " so'm";
}

function showToast(text) {
  const el = document.getElementById("toast");
  el.textContent = text;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 1800);
}

// ---------- Ekranlarni almashtirish ----------
function showScreen(name) {
  document.querySelectorAll(".screen").forEach(s => s.style.display = "none");
  document.getElementById("screen-" + name).style.display = "block";

  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  const navBtn = document.querySelector(`.nav-btn[data-tab="${name}"]`);
  if (navBtn) navBtn.classList.add("active");

  if (name === "cart") renderCart();
  if (name === "profile") renderProfile();
  window.scrollTo(0, 0);
}

function goHome() { showScreen("home"); }
function goCheckout() { showScreen("checkout"); }

// ---------- Ma'lumot yuklash ----------
async function loadCategories() {
  const res = await fetch("/api/categories");
  CATEGORIES = await res.json();
  renderCategories();
}

async function loadProducts(categoryId) {
  const url = categoryId ? `/api/products?category_id=${categoryId}` : "/api/products";
  const res = await fetch(url);
  PRODUCTS = await res.json();
  renderProducts();
}

// ---------- Bosh sahifa: kategoriyalar ----------
function renderCategories() {
  const row = document.getElementById("categories-row");
  row.innerHTML = "";

  const allChip = document.createElement("div");
  allChip.className = "category-chip" + (CURRENT_CATEGORY === null ? " active" : "");
  allChip.textContent = "Barchasi";
  allChip.onclick = () => selectCategory(null);
  row.appendChild(allChip);

  CATEGORIES.forEach(cat => {
    const chip = document.createElement("div");
    chip.className = "category-chip" + (CURRENT_CATEGORY === cat.id ? " active" : "");
    chip.textContent = `${cat.emoji} ${cat.name}`;
    chip.onclick = () => selectCategory(cat.id);
    row.appendChild(chip);
  });
}

function selectCategory(categoryId) {
  CURRENT_CATEGORY = categoryId;
  const cat = CATEGORIES.find(c => c.id === categoryId);
  document.getElementById("products-title").textContent = cat ? `${cat.emoji} ${cat.name}` : "Barcha mahsulotlar";
  renderCategories();
  loadProducts(categoryId);
}

// ---------- Mahsulotlar ro'yxati ----------
function renderProducts() {
  const grid = document.getElementById("products-grid");
  const empty = document.getElementById("products-empty");
  grid.innerHTML = "";

  if (PRODUCTS.length === 0) {
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";

  PRODUCTS.forEach(p => {
    const card = document.createElement("div");
    card.className = "product-card";
    card.onclick = () => openProduct(p.id);

    const img = p.photo_url ? `<img src="${p.photo_url}" alt="">` : `<div style="aspect-ratio:1;background:var(--bg);"></div>`;
    const priceHtml = p.has_discount
      ? `<div class="price-old">${formatPrice(p.old_price)}</div><div class="price-new discount">${formatPrice(p.price)}</div>`
      : `<div class="price-new">${formatPrice(p.price)}</div>`;

    card.innerHTML = `
      ${img}
      <div class="product-card-body">
        <div class="product-card-name">${p.name}</div>
        ${priceHtml}
      </div>
    `;
    grid.appendChild(card);
  });
}

// ---------- Mahsulot detali ----------
function openProduct(productId) {
  const p = PRODUCTS.find(x => x.id === productId);
  if (!p) return;
  CURRENT_PRODUCT_ID = productId;

  const img = p.photo_url ? `<img class="detail-photo" src="${p.photo_url}" alt="">` : `<div class="detail-photo" style="background:var(--bg);"></div>`;
  const priceHtml = p.has_discount
    ? `<span class="detail-price-old">${formatPrice(p.old_price)}</span><span class="detail-price-new discount">${formatPrice(p.price)}</span>`
    : `<span class="detail-price-new">${formatPrice(p.price)}</span>`;
  const stockHtml = p.in_stock
    ? `<span class="stock-badge in">✅ Sotuvda bor</span>`
    : `<span class="stock-badge out">❌ Hozircha yo'q</span>`;

  const currentQty = CART[p.id] || 1;

  document.getElementById("product-detail").innerHTML = `
    ${img}
    <div class="detail-body">
      <div class="detail-name">${p.name}</div>
      <div class="detail-price-row">${priceHtml}</div>
      ${stockHtml}
      <div class="detail-desc">${p.description || ""}</div>
      <div class="qty-row">
        <button class="qty-btn" onclick="changeDetailQty(-1)">−</button>
        <span class="qty-value" id="detail-qty">${currentQty}</span>
        <button class="qty-btn" onclick="changeDetailQty(1)">+</button>
      </div>
      <button class="primary-btn" ${p.in_stock ? "" : "disabled"} onclick="addToCartFromDetail(${p.id})">🛒 Savatchaga qo'shish</button>
    </div>
  `;
  showScreen("product");
}

function changeDetailQty(delta) {
  const el = document.getElementById("detail-qty");
  let val = parseInt(el.textContent, 10) + delta;
  if (val < 1) val = 1;
  el.textContent = val;
}

function addToCartFromDetail(productId) {
  const qty = parseInt(document.getElementById("detail-qty").textContent, 10);
  CART[productId] = qty;
  saveCart();
  showToast("✅ Savatchaga qo'shildi");
  if (tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
}

// ---------- Savatcha ----------
async function getProductById(id) {
  let p = PRODUCTS.find(x => x.id == id);
  if (p) return p;
  const res = await fetch(`/api/product/${id}`);
  if (!res.ok) return null;
  return await res.json();
}

async function renderCart() {
  const container = document.getElementById("cart-items");
  const empty = document.getElementById("cart-empty");
  const summary = document.getElementById("cart-summary");
  container.innerHTML = "";

  const ids = Object.keys(CART);
  if (ids.length === 0) {
    empty.style.display = "block";
    summary.style.display = "none";
    return;
  }
  empty.style.display = "none";
  summary.style.display = "block";

  let total = 0;
  for (const id of ids) {
    const p = await getProductById(id);
    if (!p) continue;
    const qty = CART[id];
    total += p.price * qty;

    const img = p.photo_url ? `<img src="${p.photo_url}" alt="">` : `<div style="width:56px;height:56px;border-radius:10px;background:var(--bg);"></div>`;

    const row = document.createElement("div");
    row.className = "cart-item";
    row.innerHTML = `
      ${img}
      <div class="cart-item-info">
        <div class="cart-item-name">${p.name}</div>
        <div class="cart-item-price">${formatPrice(p.price)} x ${qty}</div>
      </div>
      <div class="cart-item-controls">
        <button class="mini-btn" onclick="cartChangeQty(${id}, -1)">−</button>
        <span>${qty}</span>
        <button class="mini-btn" onclick="cartChangeQty(${id}, 1)">+</button>
      </div>
      <button class="remove-btn" onclick="cartRemove(${id})">🗑</button>
    `;
    container.appendChild(row);
  }

  document.getElementById("cart-total").textContent = formatPrice(total);
  updateCartBadge();
}

function cartChangeQty(id, delta) {
  const key = String(id);
  CART[key] = (CART[key] || 1) + delta;
  if (CART[key] < 1) delete CART[key];
  saveCart();
  renderCart();
}

function cartRemove(id) {
  delete CART[String(id)];
  saveCart();
  renderCart();
}

function updateCartBadge() {
  const count = Object.values(CART).reduce((a, b) => a + b, 0);
  const badge = document.getElementById("cart-badge");
  if (count > 0) {
    badge.textContent = count;
    badge.style.display = "inline-block";
  } else {
    badge.style.display = "none";
  }
}

// ---------- Checkout (buyurtma berish) ----------
async function submitOrder() {
  const name = document.getElementById("checkout-name").value.trim();
  const phone = document.getElementById("checkout-phone").value.trim();
  const address = document.getElementById("checkout-address").value.trim();
  const comment = document.getElementById("checkout-comment").value.trim();
  const errorEl = document.getElementById("checkout-error");

  if (!name || !phone || !address) {
    errorEl.textContent = "Iltimos, ism, telefon va manzilni to'ldiring";
    errorEl.style.display = "block";
    return;
  }
  errorEl.style.display = "none";

  const items = Object.entries(CART).map(([product_id, qty]) => ({
    product_id: parseInt(product_id, 10),
    qty: qty,
  }));

  if (items.length === 0) {
    errorEl.textContent = "Savatchangiz bo'sh";
    errorEl.style.display = "block";
    return;
  }

  try {
    const res = await fetch("/api/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        telegram_user_id: USER_ID,
        name, phone, address, comment, items,
      }),
    });
    const data = await res.json();

    if (!res.ok) {
      errorEl.textContent = data.error || "Xatolik yuz berdi";
      errorEl.style.display = "block";
      return;
    }

    CART = {};
    saveCart();

    if (tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
    if (tg) {
      tg.showAlert(`✅ Buyurtmangiz qabul qilindi! Raqami: #${data.order_id}`);
    } else {
      alert(`Buyurtmangiz qabul qilindi! Raqami: #${data.order_id}`);
    }

    document.getElementById("checkout-name").value = "";
    document.getElementById("checkout-phone").value = "";
    document.getElementById("checkout-address").value = "";
    document.getElementById("checkout-comment").value = "";

    showScreen("home");
  } catch (e) {
    errorEl.textContent = "Internet aloqasida muammo. Qayta urinib ko'ring.";
    errorEl.style.display = "block";
  }
}

// ---------- Profil ----------
function renderProfile() {
  const info = document.getElementById("profile-info");
  if (tgUser) {
    info.innerHTML = `
      <div class="profile-name">${tgUser.first_name || ""} ${tgUser.last_name || ""}</div>
      <div class="profile-username">${tgUser.username ? "@" + tgUser.username : ""}</div>
    `;
  } else {
    info.innerHTML = `<div class="profile-name">Mehmon</div>`;
  }
  loadOrders();
}

async function loadOrders() {
  const container = document.getElementById("profile-orders");
  const empty = document.getElementById("profile-orders-empty");
  container.innerHTML = "";

  if (!USER_ID) {
    empty.style.display = "block";
    return;
  }

  const res = await fetch(`/api/orders?user_id=${USER_ID}`);
  const orders = await res.json();

  if (orders.length === 0) {
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";

  const statusLabels = {
    "yangi": "🆕 Yangi",
    "tasdiqlandi": "📦 Tayyorlanmoqda",
    "yetkazildi": "✅ Yetkazildi",
    "bekor_qilindi": "❌ Bekor qilindi",
  };

  orders.forEach(o => {
    const itemsHtml = o.items.map(it => `<div class="order-line">${it.name} — ${it.qty} x ${formatPrice(it.price)}</div>`).join("");
    const canCancel = o.status === "yangi" || o.status === "tasdiqlandi";

    const card = document.createElement("div");
    card.className = "order-card";
    card.innerHTML = `
      <div class="order-card-top">
        <span class="order-id">#${o.id}</span>
        <span class="order-status">${statusLabels[o.status] || o.status}</span>
      </div>
      ${itemsHtml}
      <div class="order-total">Jami: ${formatPrice(o.total_price)}</div>
      ${canCancel ? `<button class="remove-btn" style="margin-top:8px;" onclick="cancelOrder(${o.id})">Bekor qilish</button>` : ""}
    `;
    container.appendChild(card);
  });
}

async function cancelOrder(orderId) {
  const res = await fetch(`/api/orders/${orderId}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_user_id: USER_ID }),
  });
  if (res.ok) {
    showToast("Buyurtma bekor qilindi");
    loadOrders();
  } else {
    showToast("Bekor qilib bo'lmadi");
  }
}

// ---------- Ishga tushirish ----------
loadCategories();
loadProducts(null);
updateCartBadge();
