// Telegram WebApp Initialization
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

// User state defaults
let userState = {
  id: 0,
  first_name: "Foydalanuvchi",
  last_name: "",
  username: "",
  income: 30,
  teamTotal: 0,
  directRefs: 0,
  activeRefs: 0,
  level: 1,
  regDate: "-",
  referrerName: "Bosh Admin (Tizim)",
  multiTier: { level_1: 0, level_2: 0, level_3: 0, total_team: 0 },
  wallets: { bep20: "", card: "", trc20: "", payeer: "" },
  botUsername: "Buyukhayot_bot"
};

// Check if launched from Telegram
if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
  const tgUser = tg.initDataUnsafe.user;
  userState.id = tgUser.id || 0;
  userState.first_name = tgUser.first_name || "Foydalanuvchi";
  userState.last_name = tgUser.last_name || "";
  userState.username = tgUser.username || "";
}

// Fetch Real Live Data from Server for this User
function fetchLiveUserData() {
  if (!userState.id) {
    updateUI();
    return;
  }

  fetch(`/api/user/profile?user_id=${userState.id}`)
    .then(res => res.json())
    .then(data => {
      if (data.success && data.user) {
        const u = data.user;
        userState.first_name = u.first_name || userState.first_name;
        userState.last_name = u.last_name || userState.last_name;
        userState.username = u.username || userState.username;
        userState.income = u.total_earned || 30;
        userState.teamTotal = u.team_total || 0;
        userState.directRefs = u.direct_referrals || 0;
        userState.activeRefs = u.active_in_marketing || 0;
        userState.level = u.current_level || 1;
        userState.regDate = u.registered_at || "-";
        userState.referrerName = u.referrer_name || "Bosh Admin (Tizim)";
        userState.multiTier = u.multi_tier || userState.multiTier;
        userState.wallets = u.wallets || userState.wallets;

        // Check if user is banned
        if (u.is_banned === 1) {
          document.body.innerHTML = `
            <div style="padding: 40px 20px; text-align: center; color: #fff; font-family: sans-serif;">
              <h2 style="color: #ef4444; margin-bottom: 12px;">⛔️ Hisobingiz Bloklangan</h2>
              <p style="color: #94a3b8; font-size: 14px;">Qoidabuzarlik sababli sizning profil cheklangan. Adminga murojaat qiling.</p>
            </div>
          `;
          return;
        }
      }
      updateUI();
    })
    .catch(err => {
      console.warn("Could not fetch live profile from API:", err);
      updateUI();
    });

  // Fetch Announcement
  fetch('/api/announcements/active')
    .then(res => res.json())
    .then(d => {
      if (d.success && d.announcement) {
        const box = document.getElementById('app-announcement');
        if (box) {
          document.getElementById('ann-title-disp').innerText = d.announcement.title || '⚡️ E\'lon';
          document.getElementById('ann-text-disp').innerText = d.announcement.text;
          box.style.display = 'block';
        }
      }
    })
    .catch(() => {});
}

function getRefLink() {
  return userState.id ? `https://t.me/${userState.botUsername}?start=ref_${userState.id}` : `https://t.me/${userState.botUsername}`;
}

// Render Data to UI
function updateUI() {
  const fullName = `${userState.first_name} ${userState.last_name}`.trim() || "Foydalanuvchi";
  const handle = userState.username ? `@${userState.username}` : (userState.id ? `ID: ${userState.id}` : "-");
  const refLink = getRefLink();

  // Header & Sidebar
  const headerName = document.getElementById("header-user-name");
  if (headerName) headerName.innerText = userState.first_name;

  const sideName = document.getElementById("sidebar-user-name");
  if (sideName) sideName.innerText = fullName;

  const sideHandle = document.getElementById("sidebar-user-handle");
  if (sideHandle) sideHandle.innerText = handle;

  const sideIncome = document.getElementById("sidebar-income");
  if (sideIncome) sideIncome.innerText = `$${userState.income}`;

  const sideTeam = document.getElementById("sidebar-team");
  if (sideTeam) sideTeam.innerText = userState.directRefs;

  const sideAvatar = document.getElementById("sidebar-avatar");
  if (sideAvatar) sideAvatar.innerText = userState.first_name.charAt(0).toUpperCase();

  // Home Stats
  const homeIncome = document.getElementById("home-total-income");
  if (homeIncome) homeIncome.innerText = `$${userState.income}`;

  const homeTeamTotal = document.getElementById("home-team-total");
  if (homeTeamTotal) homeTeamTotal.innerText = userState.teamTotal;

  const homeDirect = document.getElementById("home-direct-refs");
  if (homeDirect) homeDirect.innerText = userState.directRefs;

  const homeActive = document.getElementById("home-active-refs");
  if (homeActive) homeActive.innerText = userState.activeRefs;

  const homeLevel = document.getElementById("home-user-level");
  if (homeLevel) homeLevel.innerText = `${userState.level}-Daraja`;

  const homeRegDate = document.getElementById("home-reg-date");
  if (homeRegDate) homeRegDate.innerText = userState.regDate;

  const homeCurator = document.getElementById("home-profile-curator");
  if (homeCurator) homeCurator.innerText = `Kurator: ${userState.referrerName}`;

  const homeProfileName = document.getElementById("home-profile-fullname");
  if (homeProfileName) homeProfileName.innerText = fullName;

  const homeProfileUser = document.getElementById("home-profile-username");
  if (homeProfileUser) homeProfileUser.innerText = handle;

  const homeRefLink = document.getElementById("home-ref-link-val");
  if (homeRefLink) homeRefLink.innerText = refLink;

  // Finance
  const finBalance = document.getElementById("finance-balance");
  if (finBalance) finBalance.innerText = `$${userState.income}.00`;

  // Wallets
  if (userState.wallets) {
    if (document.getElementById("addr-bep20")) document.getElementById("addr-bep20").innerText = userState.wallets.bep20 || "Kiritilmagan";
    if (document.getElementById("addr-card")) document.getElementById("addr-card").innerText = userState.wallets.card || "Kiritilmagan";
    if (document.getElementById("addr-trc20")) document.getElementById("addr-trc20").innerText = userState.wallets.trc20 || "Kiritilmagan";
    if (document.getElementById("addr-payeer")) document.getElementById("addr-payeer").innerText = userState.wallets.payeer || "Kiritilmagan";
  }

  // Tree stats
  if (userState.multiTier) {
    if (document.getElementById("tree-l1")) document.getElementById("tree-l1").innerText = userState.multiTier.level_1 || 0;
    if (document.getElementById("tree-l2")) document.getElementById("tree-l2").innerText = userState.multiTier.level_2 || 0;
    if (document.getElementById("tree-l3")) document.getElementById("tree-l3").innerText = userState.multiTier.level_3 || 0;
  }

  // QR Code
  const qrImg = document.getElementById("dynamic-qr-img");
  if (qrImg) {
    qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(refLink)}`;
  }

  // Receipt & Business Card
  if (document.getElementById("receipt-user-display")) document.getElementById("receipt-user-display").innerText = fullName;
  if (document.getElementById("bc-name")) document.getElementById("bc-name").innerText = fullName;
  if (document.getElementById("bc-handle")) document.getElementById("bc-handle").innerText = handle;
  if (document.getElementById("bc-id")) document.getElementById("bc-id").innerText = userState.id ? `ID: ${userState.id}` : "";
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

if (menuToggle) menuToggle.addEventListener("click", openSidebar);
if (backdrop) backdrop.addEventListener("click", closeSidebar);

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
if (copyRefBtn) {
  copyRefBtn.addEventListener("click", () => {
    const link = getRefLink();
    navigator.clipboard.writeText(link).then(() => {
      showToast("✅ Referal havola nusxalandi!");
    }).catch(() => {
      showToast("Havola: " + link);
    });
  });
}

// Toast notification
function showToast(msg) {
  const toast = document.getElementById("toast");
  if (!toast) return;
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
    const link = getRefLink();
    const text = `Salom! BUYUK HAYOTGA YO'L dasturi orqali daromad olish imkoniyati. Havola orqali qo'shiling: ${link}`;
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`;
    if (tg && tg.openTelegramLink) {
      tg.openTelegramLink(shareUrl);
    } else {
      window.open(shareUrl, "_blank");
    }
  });
}

function shareCard() {
  const link = getRefLink();
  const text = `Men BUYUK HAYOTGA YO'L tizimida faoliyat yuritaman! Jamoamizga qo'shiling: ${link}`;
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`;
  window.open(shareUrl, "_blank");
}

// Init
document.addEventListener("DOMContentLoaded", () => {
  fetchLiveUserData();
});
