// Telegram WebApp Initialization
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

// User state
const userState = {
  id: 0,
  first_name: "Hamkor",
  last_name: "",
  username: "",
  income: 30,
  teamTotal: 0,
  directRefs: 0,
  activeRefs: 0,
  level: 1,
  regDate: new Date().toLocaleDateString('ru-RU'),
  botUsername: "botyangi"
};

// Check if launched from Telegram with actual user data
if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
  const tgUser = tg.initDataUnsafe.user;
  userState.id = tgUser.id || 0;
  userState.first_name = tgUser.first_name || "Hamkor";
  userState.last_name = tgUser.last_name || "";
  userState.username = tgUser.username || "";
}

// Format referral link
const refLink = userState.id ? `https://t.me/concord_bot?start=ref_${userState.id}` : `https://t.me/concord_bot`;

// Render Data to UI
function updateUI() {
  const fullName = `${userState.first_name} ${userState.last_name}`.trim();
  const handle = userState.username ? `@${userState.username}` : (userState.id ? `ID: ${userState.id}` : "-");

  // Header & Sidebar
  document.getElementById("header-user-name").innerText = userState.first_name;
  document.getElementById("sidebar-user-name").innerText = fullName;
  document.getElementById("sidebar-user-handle").innerText = handle;
  document.getElementById("sidebar-income").innerText = `$${userState.income}`;
  document.getElementById("sidebar-team").innerText = userState.directRefs;
  document.getElementById("sidebar-avatar").innerText = userState.first_name.charAt(0).toUpperCase();

  // Home Stats
  document.getElementById("home-total-income").innerText = `$${userState.income}`;
  document.getElementById("home-team-total").innerText = userState.teamTotal;
  document.getElementById("home-direct-refs").innerText = userState.directRefs;
  document.getElementById("home-active-refs").innerText = userState.activeRefs;
  document.getElementById("home-user-level").innerText = `${userState.level}-Daraja`;
  document.getElementById("home-reg-date").innerText = userState.regDate;
  document.getElementById("home-profile-fullname").innerText = fullName;
  document.getElementById("home-profile-username").innerText = handle;
  document.getElementById("home-ref-link-val").innerText = refLink;

  // Finance
  document.getElementById("finance-balance").innerText = `$${userState.income}.00`;

  // QR Code
  const qrImg = document.getElementById("dynamic-qr-img");
  if (qrImg) {
    qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(refLink)}`;
  }

  // Receipt & Business Card
  document.getElementById("receipt-user-display").innerText = fullName;
  document.getElementById("bc-name").innerText = fullName;
  document.getElementById("bc-handle").innerText = handle;
  document.getElementById("bc-id").innerText = userState.id ? `ID: ${userState.id}` : "";
}

// Navigation & Sidebar
const sidebar = document.getElementById("sidebar");
const backdrop = document.getElementById("sidebar-backdrop");
const menuToggle = document.getElementById("menu-toggle");

function openSidebar() {
  sidebar.classList.add("active");
  backdrop.classList.add("active");
}

function closeSidebar() {
  sidebar.classList.remove("active");
  backdrop.classList.remove("active");
}

menuToggle.addEventListener("click", openSidebar);
backdrop.addEventListener("click", closeSidebar);

// Page Routing
const navItems = document.querySelectorAll(".nav-item[data-page]");
const pageViews = document.querySelectorAll(".page-view");

navItems.forEach(item => {
  item.addEventListener("click", () => {
    if (item.classList.contains("disabled")) {
      showToast("Ushbu bo'lim tez kunda ishga tushadi (🚧)");
      return;
    }
    const targetPage = item.getAttribute("data-page");
    navigateTo(targetPage);
    closeSidebar();
  });
});

function navigateTo(pageId) {
  navItems.forEach(i => i.classList.remove("active"));
  pageViews.forEach(v => v.classList.remove("active"));

  const activeNav = document.querySelector(`.nav-item[data-page="${pageId}"]`);
  const activeView = document.getElementById(`view-${pageId}`);

  if (activeNav) activeNav.classList.add("active");
  if (activeView) activeView.classList.add("active");

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Copy Referral Link
const copyRefBtn = document.getElementById("copy-ref-btn");
copyRefBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(refLink).then(() => {
    showToast("✅ Referal havola nusxalandi!");
  }).catch(() => {
    showToast("Havola: " + refLink);
  });
});

// Toast notification
function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.innerText = msg;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 2400);
}

// Share on Telegram
const shareTgBtn = document.getElementById("share-tg-btn");
if (shareTgBtn) {
  shareTgBtn.addEventListener("click", () => {
    const text = `Salom! BUYUK HAYOTGA YO'L dasturi orqali daromad olish imkoniyati. Havola orqali qo'shiling: ${refLink}`;
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(refLink)}&text=${encodeURIComponent(text)}`;
    if (tg && tg.openTelegramLink) {
      tg.openTelegramLink(shareUrl);
    } else {
      window.open(shareUrl, "_blank");
    }
  });
}

function shareCard() {
  const text = `Men BUYUK HAYOTGA YO'L tizimida faoliyat yuritaman! Jamoamizga qo'shiling: ${refLink}`;
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(refLink)}&text=${encodeURIComponent(text)}`;
  window.open(shareUrl, "_blank");
}

// Init
document.addEventListener("DOMContentLoaded", () => {
  updateUI();
});
