// Telegram WebApp Initialization
const tg = window.Telegram?.WebApp;
if (tg) {
  try {
    tg.ready();
    tg.expand();
  } catch (e) {}
}

// User state defaults
let userState = {
  id: 0,
  first_name: "Foydalanuvchi",
  last_name: "",
  username: "",
  income: 0,
  teamTotal: 0,
  directRefs: 0,
  activeRefs: 0,
  level: 0,
  regDate: "-",
  referrerName: "Bosh Admin (Tizim)",
  multiTier: { level_1: 0, level_2: 0, level_3: 0, total_team: 0 },
  wallets: { bep20: "", card: "", trc20: "", payeer: "" },
  botUsername: "Buyukhayot_bot"
};

// Robust user extraction from Telegram WebApp, URL params, hash, or local cache
function detectTelegramUser() {
  // 1. Direct Telegram WebApp user object
  if (tg?.initDataUnsafe?.user?.id) {
    const u = tg.initDataUnsafe.user;
    userState.id = Number(u.id);
    userState.first_name = u.first_name || userState.first_name;
    userState.last_name = u.last_name || "";
    userState.username = u.username || "";
  }

  // 2. Query parameters (?user_id=123 or ?uid=123 or ?tgWebAppStartParam=123)
  const urlParams = new URLSearchParams(window.location.search);
  const qId = urlParams.get('user_id') || urlParams.get('uid') || urlParams.get('tgWebAppStartParam');
  if (qId && !isNaN(qId) && Number(qId) > 0) {
    userState.id = Number(qId);
  }

  // 3. Raw Telegram initData string parser
  if (!userState.id && tg?.initData) {
    try {
      const parsed = new URLSearchParams(tg.initData);
      const userRaw = parsed.get('user');
      if (userRaw) {
        const uObj = JSON.parse(userRaw);
        if (uObj.id) {
          userState.id = Number(uObj.id);
          userState.first_name = uObj.first_name || userState.first_name;
          userState.last_name = uObj.last_name || "";
          userState.username = uObj.username || "";
        }
      }
    } catch(e) {}
  }

  // 4. Hash parameters parser (e.g. #tgWebAppData=...)
  if (!userState.id && window.location.hash) {
    try {
      const hashStr = window.location.hash.substring(1);
      const hashParams = new URLSearchParams(hashStr);
      const tgData = hashParams.get('tgWebAppData');
      if (tgData) {
        const parsed = new URLSearchParams(tgData);
        const userRaw = parsed.get('user');
        if (userRaw) {
          const uObj = JSON.parse(userRaw);
          if (uObj.id) {
            userState.id = Number(uObj.id);
            userState.first_name = uObj.first_name || userState.first_name;
            userState.last_name = uObj.last_name || "";
            userState.username = uObj.username || "";
          }
        }
      }
    } catch(e) {}
  }

  // 5. Persistent storage fallback
  if (userState.id) {
    try {
      sessionStorage.setItem('bh_user_id', String(userState.id));
      localStorage.setItem('bh_user_id', String(userState.id));
    } catch (e) {}
  } else {
    try {
      const saved = sessionStorage.getItem('bh_user_id') || localStorage.getItem('bh_user_id');
      if (saved && !isNaN(saved) && Number(saved) > 0) {
        userState.id = Number(saved);
      }
    } catch (e) {}
  }
}

detectTelegramUser();

// Helper to format currency
function formatSom(amount) {
  const n = Number(amount) || 0;
  return n.toLocaleString('uz-UZ') + " so'm";
}

// Fetch Real Live Data from Server for this User
function fetchLiveUserData() {
  detectTelegramUser();

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
        userState.income = u.total_earned || 0;
        userState.teamTotal = u.team_total || 0;
        userState.directRefs = u.direct_referrals || 0;
        userState.activeRefs = u.active_in_marketing || 0;
        userState.level = u.current_level || 0;
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
  if (sideIncome) sideIncome.innerText = formatSom(userState.income);

  const sideTeam = document.getElementById("sidebar-team");
  if (sideTeam) sideTeam.innerText = userState.directRefs;

  const sideAvatar = document.getElementById("sidebar-avatar");
  if (sideAvatar) sideAvatar.innerText = userState.first_name.charAt(0).toUpperCase();

  // Home Stats
  const homeIncome = document.getElementById("home-total-income");
  if (homeIncome) homeIncome.innerText = formatSom(userState.income);

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
  if (finBalance) finBalance.innerText = formatSom(userState.income);

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

  if (pageId === "structure") {
    loadUserTree();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ====== VISUAL TEAM TREE (JAMOA SHAJARASI / STRUKTURA) ======
let currentTreeData = null;
let currentTreeViewMode = 'chart';
let currentTreeZoom = 1.0;
window._treeNodeMap = {};

function getUserLvlClass(lvl) {
  const l = parseInt(lvl) || 0;
  return `lv${Math.min(l, 5)}`;
}

function getUserLvlEmoji(lvl) {
  const icons = ['⬜', '🟢', '🔵', '🟣', '🟠', '🌟'];
  return icons[Math.min(parseInt(lvl) || 0, 5)];
}

function formatShortId(id) {
  if (!id) return '';
  const s = String(id);
  return s.length > 5 ? s.slice(-4) : s;
}

function formatShortName(first, last, uname) {
  if (uname) return `@${uname}`;
  const full = `${first || ''} ${last || ''}`.trim();
  if (full) return full.length > 10 ? full.slice(0, 9) + '…' : full;
  return 'Hamkor';
}

function countTreeDescendants(node) {
  if (!node || !node.children || !node.children.length) return 0;
  let count = node.children.length;
  node.children.forEach(c => { count += countTreeDescendants(c); });
  return count;
}

// 1. Org Chart Node Renderer (1 -> 3 -> 9 visual layout)
function renderOrgChartNode(node, isRoot = false) {
  const uid = node.user_id || 0;
  window._treeNodeMap[uid] = node;

  const shortId = uid ? (String(uid).length > 5 ? String(uid).slice(-4) : String(uid)) : '0';
  const lvl = node.current_level || 0;
  const nameDisp = isRoot ? '👑 Siz' : formatShortName(node.first_name, node.last_name, node.username);
  const isSelfClass = isRoot ? 'is-self' : '';

  const cardHtml = `
    <div class="org-node-card ${isSelfClass}" onclick="openMemberDetails(${uid})">
      <div class="org-node-id">
        <span class="org-node-id-text">${shortId}</span>
        <span class="org-level-badge lv${Math.min(lvl, 5)}">${lvl}</span>
      </div>
      <div class="org-node-name" title="${node.first_name || ''} ${node.last_name || ''}">
        ${nameDisp}
      </div>
    </div>
  `;

  if (!node.children || !node.children.length) {
    return `<li>${cardHtml}</li>`;
  }

  const childrenHtml = node.children.map(child => renderOrgChartNode(child, false)).join('');
  return `
    <li>
      ${cardHtml}
      <ul>${childrenHtml}</ul>
    </li>
  `;
}

// 2. List View Node Renderer
function renderListTreeNode(node, isRoot = false) {
  const uid = node.user_id || 0;
  window._treeNodeMap[uid] = node;

  const fullName = isRoot
    ? `👑 Siz (${node.first_name || ''} ${node.last_name || ''}`.trim() + ')'
    : `${node.first_name || ''} ${node.last_name || ''}`.trim() || 'Hamkor';

  const username = node.username ? `@${node.username}` : '';
  const lvl = node.current_level || 0;
  const hasChildren = node.children && node.children.length > 0;
  const descCount = countTreeDescendants(node);

  const countBadge = hasChildren
    ? `<span class="tree-count-badge">👥 ${node.children.length}${descCount > node.children.length ? `+${descCount - node.children.length}` : ''}</span>`
    : '';

  const cardClass = isRoot ? 'tree-person-card root-card' : 'tree-person-card';
  const avatarIcon = isRoot ? '👑' : getUserLvlEmoji(lvl);

  let contactBtn = '';
  if (!isRoot && node.user_id) {
    const contactUrl = node.username ? `https://t.me/${node.username}` : `tg://user?id=${node.user_id}`;
    contactBtn = `<a href="${contactUrl}" target="_blank" class="tree-contact-btn" title="Telegramda yozish" onclick="event.stopPropagation();">💬</a>`;
  }

  const html = `
    <div class="tree-person">
      <div class="${cardClass}" onclick="openMemberDetails(${uid})">
        <div class="tree-avatar">${avatarIcon}</div>
        <div class="tree-info">
          <div class="tree-name">${fullName} ${countBadge}</div>
          <div class="tree-meta">
            <code style="font-size:10.5px; color:#94a3b8;">${node.user_id ? `ID: ${node.user_id}` : ''}</code>
            ${username ? `<span style="color:#38bdf8;">${username}</span>` : ''}
          </div>
        </div>
        <span class="tree-level-badge">${lvl}-Daraja</span>
        ${contactBtn}
      </div>
    </div>
    ${hasChildren ? `<div class="tree-children">
      ${node.children.map(child => `
        <div class="tree-connector">
          ${renderListTreeNode(child, false)}
        </div>
      `).join('')}
    </div>` : ''}
  `;
  return html;
}

// Switch between Org Chart view and List view
function switchTreeView(mode) {
  currentTreeViewMode = mode;
  document.querySelectorAll('.tree-tab-btn').forEach(b => b.classList.remove('active'));

  const activeBtn = document.getElementById(mode === 'chart' ? 'btn-view-chart' : 'btn-view-list');
  if (activeBtn) activeBtn.classList.add('active');

  const zoomTools = document.getElementById('tree-zoom-tools');
  if (zoomTools) zoomTools.style.display = mode === 'chart' ? 'inline-flex' : 'none';

  renderCurrentTree();
}

// Zoom controls
function zoomTree(delta) {
  currentTreeZoom = Math.min(Math.max(currentTreeZoom + delta, 0.45), 1.6);
  const root = document.getElementById('org-chart-root');
  if (root) {
    root.style.transform = `scale(${currentTreeZoom})`;
  }
}

function resetTreeZoom() {
  currentTreeZoom = 1.0;
  const root = document.getElementById('org-chart-root');
  if (root) {
    root.style.transform = `scale(1)`;
  }
  centerTreeScroll();
}

function centerTreeScroll() {
  const scrollArea = document.getElementById('org-scroll-area');
  if (scrollArea) {
    setTimeout(() => {
      scrollArea.scrollLeft = (scrollArea.scrollWidth - scrollArea.clientWidth) / 2;
    }, 50);
  }
}

// Open Member Details Modal
function openMemberDetails(uid) {
  const node = window._treeNodeMap ? window._treeNodeMap[uid] : null;
  if (!node) return;

  const fullName = `${node.first_name || ''} ${node.last_name || ''}`.trim() || 'Hamkor';
  const uname = node.username ? `@${node.username}` : 'Mavjud emas';
  const lvl = node.current_level || 0;
  const descCount = countTreeDescendants(node);
  const directCount = node.children ? node.children.length : 0;

  document.getElementById('m-modal-name').innerText = fullName;
  document.getElementById('m-modal-handle').innerText = uname;
  document.getElementById('m-modal-id').innerText = node.user_id || '-';
  document.getElementById('m-modal-date').innerText = node.registered_at ? node.registered_at.slice(0, 10) : '-';
  document.getElementById('m-modal-level').innerText = `${lvl}-Daraja`;
  document.getElementById('m-modal-refs').innerText = `👥 ${directCount} ta to'g'ridan-to'g'ri (${descCount} jami)`;
  document.getElementById('m-modal-avatar').innerText = getUserLvlEmoji(lvl);

  const chatBtn = document.getElementById('m-modal-chat-btn');
  if (chatBtn) {
    chatBtn.href = node.username ? `https://t.me/${node.username}` : `tg://user?id=${node.user_id}`;
  }

  const modal = document.getElementById('member-detail-modal');
  if (modal) modal.classList.add('active');
}

function closeMemberModal(e) {
  const modal = document.getElementById('member-detail-modal');
  if (modal) modal.classList.remove('active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

function renderCurrentTree() {
  const container = document.getElementById("user-tree-container");
  if (!container || !currentTreeData) return;

  window._treeNodeMap = {};

  if (currentTreeViewMode === 'chart') {
    container.innerHTML = `
      <div class="org-chart-root" id="org-chart-root" style="transform: scale(${currentTreeZoom});">
        <div class="org-chart-tree">
          <ul>
            ${renderOrgChartNode(currentTreeData, true)}
          </ul>
        </div>
      </div>
    `;
    centerTreeScroll();
  } else {
    container.innerHTML = `
      <div class="user-tree-wrap">
        ${renderListTreeNode(currentTreeData, true)}
      </div>
    `;
  }
}

function loadUserTree() {
  const container = document.getElementById("user-tree-container");
  if (!container) return;

  if (!userState.id) {
    container.innerHTML = `
      <div class="tree-empty-state">
        <div class="tree-empty-icon">🌱</div>
        <div class="tree-empty-title">Struktura</div>
        <div class="tree-empty-desc">Ma'lumotlar yuklanmoqda yoki Telegram orqali ochilmagan.</div>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div style="text-align: center; color: var(--text-muted); padding: 30px 10px;">
      <div style="font-size: 28px; margin-bottom: 8px;">⏳</div>
      <div>Struktura yuklanmoqda...</div>
    </div>
  `;

  fetch(`/api/user/tree?user_id=${userState.id}`)
    .then(res => res.json())
    .then(d => {
      if (!d.success || !d.tree) {
        container.innerHTML = `
          <div class="tree-empty-state">
            <div class="tree-empty-icon">⚠️</div>
            <div class="tree-empty-title">Tuzilma topilmadi</div>
            <div class="tree-empty-desc">Jamoa ma'lumotlarini yuklab bo'lmadi. Qayta urinib ko'ring.</div>
          </div>
        `;
        return;
      }

      const t = d.tree;
      currentTreeData = t;

      const totalDesc = countTreeDescendants(t);
      const l1Count = t.children ? t.children.length : 0;
      let l2Count = 0;
      if (t.children) {
        t.children.forEach(c => {
          if (c.children) l2Count += c.children.length;
        });
      }

      // Update stat pills
      const totalEl = document.getElementById("tree-stat-total");
      if (totalEl) totalEl.innerText = totalDesc;

      const l1El = document.getElementById("tree-stat-l1");
      if (l1El) l1El.innerText = `${l1Count} / 3`;

      const l2El = document.getElementById("tree-stat-l2");
      if (l2El) l2El.innerText = `${l2Count} / 9`;

      const lvlEl = document.getElementById("tree-stat-level");
      if (lvlEl) lvlEl.innerText = `${t.current_level || userState.level || 0}-Daraja`;

      if (!t.children || t.children.length === 0) {
        container.innerHTML = `
          <div class="tree-empty-state">
            <div class="tree-empty-icon">🌱</div>
            <div class="tree-empty-title">Sizda hali hamkorlar yo'q</div>
            <div class="tree-empty-desc">
              Referal havolangiz orqali 3 ta do'stingizni taklif qiling va 1-bosqich shajarangizni yarating!
            </div>
            <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
              <button class="action-btn gold-btn" style="padding: 9px 18px; font-size: 13px;" onclick="navigateTo('partners')">
                🔗 Referal Havola Olish
              </button>
            </div>
          </div>
        `;
        return;
      }

      renderCurrentTree();
    })
    .catch(err => {
      console.error("Error loading user tree:", err);
      container.innerHTML = `
        <div class="tree-empty-state">
          <div class="tree-empty-icon">❌</div>
          <div class="tree-empty-title">Xatolik yuz berdi</div>
          <div class="tree-empty-desc">Server bilan bog'lanishda xatolik. Iltimos qayta urining.</div>
        </div>
      `;
    });
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
