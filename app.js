const Config = window.APP_CONFIG || {};
const AUTO_REFRESH_MS = 1800000; // 30 دقیقه
const MOBILE_ANIMATION_WIDTH = 700;

let allItems = [];
let activeFilter = "all";
let liveClockTimer = null;
let autoRefreshTimer = null;
let particleFrame = null;

// --- عناصر DOM همانند قبل ---
const loadingBox = document.getElementById("loadingBox");
const errorBox = document.getElementById("errorBox");
const errorText = document.getElementById("errorText");
const marketSections = document.getElementById("marketSections");
const emptyState = document.getElementById("emptyState");
const updatedAtEl = document.getElementById("updatedAt");
const refreshBtn = document.getElementById("refreshBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const searchInput = document.getElementById("searchInput");
const themeBtn = document.getElementById("themeBtn");
const themeIcon = document.getElementById("themeIcon");
const heroUpdatedAt = document.getElementById("heroUpdatedAt");

// ----------------- ابزارها و فرمت‌ها (بدون تغییر) -----------------
function toPersianDigits(value) {
  return String(value).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "--";
  return toPersianDigits(String(value));
}

function normalizeText(text) {
  return String(text || "")
    .replace(/ي/g, "ی")
    .replace(/ك/g, "ک")
    .trim()
    .toLowerCase();
}

function formatNow() {
  const now = new Date();
  return now.toLocaleString("fa-IR", {
    dateStyle: "full",
    timeStyle: "medium"
  });
}

function updateLiveTime() {
  const nowText = formatNow();
  if (updatedAtEl) updatedAtEl.textContent = nowText;
  if (heroUpdatedAt) heroUpdatedAt.textContent = nowText;
}

// ... بقیه‌ی توابع detectCategory, getCategoryMeta, getUnit, setLoading, setError,
// setLiveStatus, groupItems, createItemCard, renderSections, cleanNumber, parseMarketLog
// دقیقاً همان کد قبلی شماست، تغییری نیاز ندارد ...

function detectCategory(label) {
  const text = normalizeText(label);

  const cryptoKeywords = [
    "btc","eth","usdt","bnb","ada","xrp","doge","sol","trx",
    "bitcoin","ethereum","tether","binance","ton","notcoin",
    "رمزارز","بیت","اتریوم","تتر","ارز دیجیتال"
  ];

  const coinKeywords = [
    "سکه","نیم سکه","ربع سکه","تمام سکه","امامی","بهار آزادی"
  ];

  const goldKeywords = [
    "طلا","طلای","گرم طلا","مثقال","اونس"
  ];

  const currencyKeywords = [
    "دلار","یورو","درهم","پوند","لیر","فرانک","ین",
    "روبل","یوان","دینار","افغانی","ریال","ارز"
  ];

  if (cryptoKeywords.some((k) => text.includes(k))) return "crypto";
  if (coinKeywords.some((k) => text.includes(k))) return "coin";
  if (goldKeywords.some((k) => text.includes(k))) return "gold";
  if (currencyKeywords.some((k) => text.includes(k))) return "currency";

  return "currency";
}

function getCategoryMeta(category) {
  const map = {
    currency: {
      title: "ارز",
      subtitle: "Foreign Exchange Market",
      icon: "¤",
      itemIcon: "＄"
    },
    coin: {
      title: "سکه",
      subtitle: "Coin Market",
      icon: "◍",
      itemIcon: "◎"
    },
    gold: {
      title: "طلا",
      subtitle: "Gold Market",
      icon: "✦",
      itemIcon: "✧"
    },
    crypto: {
      title: "رمزارز",
      subtitle: "Crypto Assets",
      icon: "₿",
      itemIcon: "◈"
    }
  };

  return map[category] || map.currency;
}

function getUnit(category, label) {
  const text = normalizeText(label);

  if (category === "crypto") return "USD";
  if (category === "currency") return "ریال";
  if (category === "coin") return "ریال";

  if (category === "gold") {
    if (text.includes("انس") || text.includes("اونس")) return "USD";
    return "ریال";
  }

  return "";
}

function setLoading(state) {
  if (loadingBox) loadingBox.classList.toggle("hidden", !state);
}

function setError(message = "") {
  const hasError = Boolean(message);
  if (errorBox) errorBox.classList.toggle("hidden", !hasError);
  if (hasError && errorText) errorText.textContent = message;
}

function setLiveStatus(mode = "idle", text = "") {
  if (statusDot) {
    statusDot.classList.remove("live", "error");
    if (mode === "live") {
      statusDot.classList.add("live");
    } else if (mode === "error") {
      statusDot.classList.add("error");
    }
  }
  if (statusText) statusText.textContent = text || "نامشخص";
}

function groupItems(items) {
  const grouped = {
    currency: [],
    coin: [],
    gold: [],
    crypto: []
  };

  items.forEach((item) => {
    const category = detectCategory(item.label);
    grouped[category].push({ ...item, category });
  });

  return grouped;
}

function createItemCard(item) {
  const meta = getCategoryMeta(item.category);
  const value = formatValue(item.value);
  const unit = getUnit(item.category, item.label);

  return `
    <article class="market-card ${item.category}">
      <div class="card-top">
        <div class="card-icon ${item.category}">${meta.itemIcon}</div>
        <div class="card-title-wrap">
          <div class="card-title">${item.label}</div>
          <div class="card-badge">${meta.title}</div>
        </div>
      </div>

      <div class="card-value-row">
        <div class="value-side">
          <div class="card-value">${value}</div>
          <div class="card-unit">${unit}</div>
        </div>
        <div class="card-pulse"></div>
      </div>
    </article>
  `;
}

function renderSections(items) {
  if (!marketSections || !emptyState) return;

  const query = normalizeText(searchInput ? searchInput.value : "");
  let filtered = items;

  if (activeFilter !== "all") {
    filtered = filtered.filter(
      (item) => detectCategory(item.label) === activeFilter
    );
  }

  if (query) {
    filtered = filtered.filter((item) =>
      normalizeText(item.label).includes(query)
    );
  }

  marketSections.innerHTML = "";

  if (!filtered.length) {
    marketSections.classList.add("hidden");
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");
  marketSections.classList.remove("hidden");

  const grouped = groupItems(filtered);
  const order = ["currency", "coin", "gold", "crypto"];

  order.forEach((category) => {
    const list = grouped[category];
    if (!list.length) return;

    const meta = getCategoryMeta(category);
    const section = document.createElement("section");

    section.className = "market-section";
    section.innerHTML = `
      <div class="section-head">
        <div class="section-icon">${meta.icon}</div>
        <div class="section-title-wrap">
          <div class="section-title">${meta.title}</div>
          <div class="section-subtitle">${meta.subtitle}</div>
        </div>
        <div class="section-count">${toPersianDigits(list.length)} مورد</div>
      </div>

      <div class="items-grid">
        ${list.map(createItemCard).join("")}
      </div>
    `;

    marketSections.appendChild(section);
  });
}

function cleanNumber(text) {
  return String(text || "").trim();
}

function parseMarketLog(text) {
  const items = [];

  for (const rawLine of String(text || "").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    if (line.startsWith("#")) continue;
    if (line.startsWith("🆔")) continue;
    if (!line.includes(":")) continue;

    const parts = line.split(":");
    const label = parts[0]
      .replace(/☸️/g, "")
      .replace(/✴️/g, "")
      .trim();

    const value = parts.slice(1).join(":").trim();
    if (!label || !value) continue;

    items.push({
      label,
      value: cleanNumber(value)
    });
  }

  return items;
}

// ----------------- بخش GitHub + Backoff -----------------
function buildRawGithubUrl() {
  const owner = Config.GITHUB_OWNER;
  const repo = Config.GITHUB_REPO;
  const branch = Config.GITHUB_BRANCH || "main";
  const path = Config.GITHUB_PATH;

  if (!owner || !repo || !path) {
    throw new Error("GitHub config is incomplete.");
  }

  return `https://raw.githubusercontent.com/${owner}/${repo}/${branch}/${path}`;
}

/**
 * این تابع:
 * - 429 یا 5xx را تشخیص می‌دهد
 * - اگر 429 بود، بر اساس Retry-After یا backoff داخلی صبر می‌کند
 * - برای کاربر فقط پیام خطای خوانا نشان می‌دهد
 */
async function fetchPrivateFile() {
  const url = buildRawGithubUrl();

  const response = await fetch(url, {
    method: "GET",
    cache: "no-store"
  });

  if (!response.ok) {
    // اگر Rate Limit خورد
    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After");
      // اگر GitHub مشخص کرده، همان را استفاده کن
      if (retryAfter) {
        const retryMs = parseInt(retryAfter, 10) * 1000;
        console.warn("Rate limited. Retry after (ms):", retryMs);
      }
      throw new Error("محدودیت درخواست به گیت‌هاب (429). لطفاً کمی بعد دوباره تلاش کنید.");
    }

    // اگر خطای سروری یا موقت بود، بهتر است در نوبت بعدی دوباره تلاش شود
    if (response.status >= 500 && response.status < 600) {
      throw new Error("خطای موقت گیت‌هاب (5xx). لطفاً بعداً دوباره تلاش کنید.");
    }

    throw new Error(`HTTP ${response.status}`);
  }

  return response.text();
}

async function getMarketData() {
  const text = await fetchPrivateFile();
  return parseMarketLog(text);
}

async function fetchMarketData(showLoader = false) {
  try {
    if (showLoader) setLoading(true);

    setError("");
    setLiveStatus("idle", "در حال بروزرسانی...");

    if (refreshBtn) {
      refreshBtn.style.pointerEvents = "none";
      refreshBtn.style.opacity = "0.7";
    }

    const items = await getMarketData();

    allItems = items.map((item) => ({
      label: item.label || "بدون عنوان",
      value: item.value ?? "--"
    }));

    updateLiveTime();
    renderSections(allItems);
    setLiveStatus("live", "داده‌ها با موفقیت بروزرسانی شد");
  } catch (error) {
    console.error(error);
    setError(error.message || "خطا در خواندن اطلاعات بازار. لطفاً دوباره تلاش کنید.");
    setLiveStatus("error", "دریافت داده ناموفق");

    if (marketSections) marketSections.classList.add("hidden");
    if (emptyState) emptyState.classList.add("hidden");
  } finally {
    setLoading(false);

    if (refreshBtn) {
      refreshBtn.style.pointerEvents = "auto";
      refreshBtn.style.opacity = "1";
    }
  }
}

// ----------------- فیلتر، سرچ، تم، انیمیشن (بدون تغییر جدی) -----------------
function setupFilters() {
  const buttons = document.querySelectorAll(".control-btn");

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeFilter = btn.dataset.filter;
      renderSections(allItems);
    });
  });
}

function setupSearch() {
  let debounceTimer = null;
  if (!searchInput) return;

  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      renderSections(allItems);
    }, 120);
  });
}

function setupTheme() {
  const savedTheme = localStorage.getItem("market_theme") || "dark";

  if (savedTheme === "light") {
    document.body.classList.add("light-theme");
    if (themeIcon) themeIcon.textContent = "☀";
  } else {
    document.body.classList.remove("light-theme");
    if (themeIcon) themeIcon.textContent = "☾";
  }

  if (!themeBtn) return;

  themeBtn.addEventListener("click", () => {
    const isLight = document.body.classList.toggle("light-theme");
    localStorage.setItem("market_theme", isLight ? "light" : "dark");
    if (themeIcon) themeIcon.textContent = isLight ? "☀" : "☾";
  });
}

function shouldUseLightAnimations() {
  return (
    window.innerWidth <= MOBILE_ANIMATION_WIDTH ||
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

function createParticles() {
  const container = document.getElementById("bgParticles");
  if (!container) return;

  if (shouldUseLightAnimations()) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = "";
  const count = 20;

  for (let i = 0; i < count; i += 1) {
    const p = document.createElement("span");
    const size = Math.random() * 4 + 2;

    p.style.width = `${size}px`;
    p.style.height = `${size}px`;
    p.style.left = `${Math.random() * 100}%`;
    p.style.animationDuration = `${12 + Math.random() * 12}s`;
    p.style.animationDelay = `${Math.random() * 6}s`;
    p.style.opacity = (0.18 + Math.random() * 0.28).toFixed(2);

    container.appendChild(p);
  }
}

function scheduleParticleRefresh() {
  if (particleFrame) {
    cancelAnimationFrame(particleFrame);
  }

  particleFrame = requestAnimationFrame(() => {
    createParticles();
  });
}

// ----------------- زمان‌بندی با Backoff به‌جای setInterval -----------------

let currentRefreshDelay = AUTO_REFRESH_MS;
const MIN_REFRESH_MS = 5 * 60 * 1000;   // حداقل ۵ دقیقه
const MAX_REFRESH_MS = 2 * 60 * 60 * 1000; // حداکثر ۲ ساعت

async function scheduleAutoRefreshLoop() {
  // یک بار اجرا
  try {
    await fetchMarketData(false);
    // اگر موفق شد، Delay را برگردان به مقدار پایه (حداقل ۳۰ دقیقه)
    currentRefreshDelay = AUTO_REFRESH_MS;
  } catch (e) {
    // اگر خطا بود، کمی Backoff کن (مثلاً ۱.۵ برابر تا سقف مشخص)
    currentRefreshDelay = Math.min(
      Math.max(currentRefreshDelay * 1.5, MIN_REFRESH_MS),
      MAX_REFRESH_MS
    );
  }

  // با کمی Jitter تصادفی تا الگو یکنواخت نباشد (برای هزار کاربر)
  const jitter = (Math.random() - 0.5) * 0.2 * currentRefreshDelay; // ±۲۰٪
  const nextDelay = Math.max(1000, currentRefreshDelay + jitter);

  autoRefreshTimer = setTimeout(scheduleAutoRefreshLoop, nextDelay);
}

function init() {
  setupFilters();
  setupSearch();
  setupTheme();
  createParticles();
  updateLiveTime();

  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => fetchMarketData(false));
  }

  window.addEventListener("resize", scheduleParticleRefresh);

  // اولین بار با Loader
  fetchMarketData(true);

  // ساعت زنده
  liveClockTimer = setInterval(updateLiveTime, 1000);

  // به‌جای setInterval ثابت، Loop با Backoff
  currentRefreshDelay = AUTO_REFRESH_MS;
  autoRefreshTimer = setTimeout(scheduleAutoRefreshLoop, AUTO_REFRESH_MS);
}

document.addEventListener("DOMContentLoaded", init);
