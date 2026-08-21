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
  isAdmin: false,
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
        // Always keep Telegram name if server returns generic placeholder
        if (u.first_name && u.first_name !== 'Hamkor') userState.first_name = u.first_name;
        if (u.last_name) userState.last_name = u.last_name;
        if (u.username) userState.username = u.username;
        userState.income = u.total_earned || 0;
        userState.teamTotal = u.team_total || 0;
        userState.directRefs = u.direct_referrals || 0;
        userState.activeRefs = u.active_in_marketing || 0;
        userState.level = u.current_level || 0;
        userState.regDate = u.registered_at || "-";
        userState.referrerName = u.referrer_name || "Bosh Admin (Tizim)";
        userState.multiTier = u.multi_tier || userState.multiTier;
        userState.wallets = u.wallets || userState.wallets;
        userState.isAdmin = Boolean(u.is_admin);

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

// =========================================================
// REFERRAL TREE CANVAS ENGINE (EXACT USER SPECIFICATION)
// =========================================================
const CANVAS_NODE_W    = 112;
const CANVAS_NODE_GAP  = 26;
const CANVAS_LEVEL_H   = 128;
const CANVAS_MIN_LEAF_W = CANVAS_NODE_W + CANVAS_NODE_GAP;
const CANVAS_CARD_H    = 64;
const ZOOM_MIN         = 0.15;
const ZOOM_MAX         = 2.2;

let canvasRoot = null;
let flatIndex = [];
const nodeElPool = new Map();
let visibleNodes = [];
let contentW = 0, contentH = 0;
let panX = 40, panY = 20, zoom = 1;
let selectedUid = null;
let dragging = false, dragStartX = 0, dragStartY = 0, panStartX = 0, panStartY = 0;
let lastTouchDist = null, lastTouchMid = null;
let canvasListenersAttached = false;

// Convert API Tree Data to Canvas Tree Model
function buildCanvasTree(apiNode, level = 0, parent = null) {
  const isRoot = (level === 0);
  const fullName = isRoot
    ? (apiNode.first_name ? `${apiNode.first_name} ${apiNode.last_name || ''}`.trim() : (userState.first_name || 'Siz'))
    : (`${apiNode.first_name || ''} ${apiNode.last_name || ''}`.trim() || 'Hamkor');
  
  const dispName = isRoot ? '👑 Siz' : (apiNode.username ? `@${apiNode.username}` : fullName);
  const rawId = apiNode.user_id ? String(apiNode.user_id) : String(1000 + Math.floor(Math.random() * 9000));
  const shortId = rawId.length > 6 ? rawId.slice(-5) : rawId;

  const node = {
    uid: flatIndex.length,
    user_id: apiNode.user_id || 0,
    id: shortId,
    fullId: rawId,
    name: dispName,
    fullName: fullName,
    username: apiNode.username || '',
    level: apiNode.current_level !== undefined ? apiNode.current_level : level,
    treeDepth: level,
    parent: parent,
    children: [],
    registered_at: apiNode.registered_at || '',
    total_earned: apiNode.total_earned || 0,
    status: apiNode.status || "🌱 Boshlang'ich",
    expanded: level < 2
  };

  flatIndex.push(node);

  if (apiNode.children && Array.isArray(apiNode.children)) {
    apiNode.children.forEach(child => {
      node.children.push(buildCanvasTree(child, level + 1, node));
    });
  }

  return node;
}

// Tree Layout Calculations
function computeWidth(node) {
  if (!node.expanded || node.children.length === 0) {
    node._w = CANVAS_MIN_LEAF_W;
    return node._w;
  }
  let w = 0;
  node.children.forEach(c => { w += computeWidth(c); });
  node._w = Math.max(w, CANVAS_MIN_LEAF_W);
  return node._w;
}

function computePosition(node, x, y) {
  node._x = x + node._w / 2;
  node._y = y;
  if (node.expanded && node.children.length) {
    let cx = x;
    node.children.forEach(c => {
      computePosition(c, cx, y + CANVAS_LEVEL_H);
      cx += c._w;
    });
  }
}

function collectVisible(node, arr) {
  arr.push(node);
  if (node.expanded) {
    node.children.forEach(c => collectVisible(c, arr));
  }
}

function layoutTree() {
  if (!canvasRoot) return;
  computeWidth(canvasRoot);
  computePosition(canvasRoot, 0, 40);
  visibleNodes = [];
  collectVisible(canvasRoot, visibleNodes);
  contentW = canvasRoot._w || 300;
  const maxDepth = visibleNodes.length ? Math.max(...visibleNodes.map(n => n.treeDepth || 0)) : 0;
  contentH = (maxDepth + 1) * CANVAS_LEVEL_H + 80;
}

// Create Card DOM Element for Canvas
function makeNodeEl(node) {
  const el = document.createElement('div');
  el.className = 'node';
  el.dataset.uid = node.uid;

  const card = document.createElement('div');
  card.className = 'card';

  const idPill = document.createElement('div');
  idPill.className = 'id-pill';
  idPill.textContent = node.id;

  if (node.children.length) {
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = node.children.length;
    idPill.appendChild(badge);
  }

  const namePill = document.createElement('div');
  namePill.className = 'name-pill';
  namePill.textContent = node.name;
  namePill.title = `${node.fullName} (${node.fullId})`;

  card.appendChild(idPill);
  card.appendChild(namePill);
  el.appendChild(card);

  if (node.children.length) {
    const dot = document.createElement('div');
    dot.className = 'expand-dot';
    dot.textContent = node.expanded ? '−' : '+';
    el.appendChild(dot);
  }

  el.addEventListener('click', (e) => {
    e.stopPropagation();
    onCanvasNodeClick(node);
  });

  return el;
}

// Render Canvas Tree
function renderCanvasTree() {
  if (!canvasRoot) return;
  layoutTree();

  const viewport = document.getElementById('viewport');
  const linksSvg = document.getElementById('links');
  if (!viewport || !linksSvg) return;

  viewport.style.width = contentW + 'px';
  viewport.style.height = contentH + 'px';
  linksSvg.setAttribute('width', contentW);
  linksSvg.setAttribute('height', contentH);
  linksSvg.setAttribute('viewBox', `0 0 ${contentW} ${contentH}`);

  const seen = new Set();
  visibleNodes.forEach(node => {
    seen.add(node.uid);
    let el = nodeElPool.get(node.uid);
    if (!el) {
      el = makeNodeEl(node);
      nodeElPool.set(node.uid, el);
      viewport.appendChild(el);
    } else {
      const dot = el.querySelector('.expand-dot');
      if (dot) dot.textContent = node.expanded ? '−' : '+';
    }
    el.style.left = node._x + 'px';
    el.style.top  = node._y + 'px';
  });

  nodeElPool.forEach((el, uid) => {
    if (!seen.has(uid)) {
      el.remove();
      nodeElPool.delete(uid);
    }
  });

  drawCanvasLinks();
  applyTreeHighlight();
  applyCanvasTransform();
}

function drawCanvasLinks() {
  const linksSvg = document.getElementById('links');
  if (!linksSvg) return;
  let html = '';
  visibleNodes.forEach(node => {
    if (!node.expanded || node.children.length === 0) return;
    const px = node._x, py = node._y + CANVAS_CARD_H;
    const midY = py + (CANVAS_LEVEL_H - CANVAS_CARD_H) / 2;
    node.children.forEach(child => {
      const cx = child._x, cy = child._y;
      const d = `M ${px} ${py} L ${px} ${midY} L ${cx} ${midY} L ${cx} ${cy}`;
      html += `<path data-from="${node.uid}" data-to="${child.uid}" d="${d}"></path>`;
    });
  });
  linksSvg.innerHTML = html;
}

function onCanvasNodeClick(node) {
  if (node.children.length) {
    node.expanded = !node.expanded;
  }
  selectedUid = node.uid;
  renderCanvasTree();
  openMemberDetails(node.user_id || node.uid, node);
}

function collectSubtreeUids(node, set) {
  set.add(node.uid);
  node.children.forEach(c => collectSubtreeUids(c, set));
}

function applyTreeHighlight() {
  const linksSvg = document.getElementById('links');
  if (!linksSvg) return;

  if (selectedUid === null) {
    nodeElPool.forEach(el => { el.classList.remove('dim', 'lit'); });
    linksSvg.querySelectorAll('path').forEach(p => p.classList.remove('dim', 'lit'));
    return;
  }
  const selNode = flatIndex.find(n => n.uid === selectedUid);
  if (!selNode) return;
  const lit = new Set();
  collectSubtreeUids(selNode, lit);

  nodeElPool.forEach((el, uid) => {
    if (lit.has(uid)) { el.classList.add('lit'); el.classList.remove('dim'); }
    else { el.classList.add('dim'); el.classList.remove('lit'); }
  });
  linksSvg.querySelectorAll('path').forEach(p => {
    const from = Number(p.dataset.from), to = Number(p.dataset.to);
    if (lit.has(from) && lit.has(to)) { p.classList.add('lit'); p.classList.remove('dim'); }
    else { p.classList.add('dim'); p.classList.remove('lit'); }
  });
}

// Pan & Zoom Engine
function applyCanvasTransform() {
  const viewport = document.getElementById('viewport');
  const zoomPct = document.getElementById('zoomPct');
  if (viewport) {
    viewport.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
  }
  if (zoomPct) {
    zoomPct.textContent = Math.round(zoom * 100) + '%';
  }
}

function zoomAt(mx, my, newZoom) {
  newZoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, newZoom));
  const wx = (mx - panX) / zoom;
  const wy = (my - panY) / zoom;
  panX = mx - wx * newZoom;
  panY = my - wy * newZoom;
  zoom = newZoom;
  applyCanvasTransform();
}

function fitToScreen() {
  const stage = document.getElementById('stage');
  if (!stage || !contentW) return;
  const r = stage.getBoundingClientRect();
  const width = (r.width > 0 ? r.width : (stage.clientWidth || stage.offsetWidth || window.innerWidth || 360));
  const height = (r.height > 0 ? r.height : (stage.clientHeight || stage.offsetHeight || 500));
  const pad = 30;
  const scaleX = (width - pad * 2) / contentW;
  const scaleY = (height - pad * 2) / Math.max(contentH, 200);
  zoom = Math.min(1.15, Math.max(ZOOM_MIN, Math.min(scaleX, scaleY)));
  panX = (width - contentW * zoom) / 2;
  panY = 30;
  applyCanvasTransform();
}

function touchDist(t) { return Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY); }
function touchMid(t) { return { x: (t[0].clientX + t[1].clientX) / 2, y: (t[0].clientY + t[1].clientY) / 2 }; }

function attachCanvasListeners() {
  if (canvasListenersAttached) return;
  canvasListenersAttached = true;

  const stage = document.getElementById('stage');
  if (!stage) return;

  stage.addEventListener('mousedown', (e) => {
    dragging = true;
    stage.classList.add('dragging');
    dragStartX = e.clientX; dragStartY = e.clientY;
    panStartX = panX; panStartY = panY;
  });

  window.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    panX = panStartX + (e.clientX - dragStartX);
    panY = panStartY + (e.clientY - dragStartY);
    applyCanvasTransform();
  });

  window.addEventListener('mouseup', () => {
    dragging = false;
    stage.classList.remove('dragging');
  });

  stage.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      dragging = true;
      dragStartX = e.touches[0].clientX; dragStartY = e.touches[0].clientY;
      panStartX = panX; panStartY = panY;
    } else if (e.touches.length === 2) {
      dragging = false;
      lastTouchDist = touchDist(e.touches);
      lastTouchMid = touchMid(e.touches);
    }
  }, { passive: true });

  stage.addEventListener('touchmove', (e) => {
    if (e.touches.length === 1 && dragging) {
      panX = panStartX + (e.touches[0].clientX - dragStartX);
      panY = panStartY + (e.touches[0].clientY - dragStartY);
      applyCanvasTransform();
    } else if (e.touches.length === 2) {
      const dist = touchDist(e.touches);
      const mid  = touchMid(e.touches);
      if (lastTouchDist) {
        const scaleDelta = dist / lastTouchDist;
        zoomAt(mid.x, mid.y, zoom * scaleDelta);
      }
      lastTouchDist = dist; lastTouchMid = mid;
    }
  }, { passive: true });

  stage.addEventListener('touchend', () => {
    dragging = false;
    lastTouchDist = null;
  });

  stage.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = stage.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const delta = -e.deltaY * 0.0016;
    zoomAt(mx, my, zoom * (1 + delta));
  }, { passive: false });

  document.getElementById('zoomInBtn')?.addEventListener('click', () => {
    const r = stage.getBoundingClientRect();
    zoomAt(r.width / 2, r.height / 2, zoom * 1.25);
  });
  document.getElementById('zoomOutBtn')?.addEventListener('click', () => {
    const r = stage.getBoundingClientRect();
    zoomAt(r.width / 2, r.height / 2, zoom * 0.8);
  });
  document.getElementById('fitBtn')?.addEventListener('click', (e) => {
    e.stopPropagation();
    fitToScreen();
  });
  document.getElementById('expandAllBtn')?.addEventListener('click', (e) => {
    e.stopPropagation();
    flatIndex.forEach(n => { if (n.children.length) n.expanded = true; });
    renderCanvasTree();
    requestAnimationFrame(fitToScreen);
  });
  document.getElementById('collapseAllBtn')?.addEventListener('click', (e) => {
    e.stopPropagation();
    flatIndex.forEach(n => { n.expanded = (n.treeDepth < 1); });
    selectedUid = null;
    renderCanvasTree();
    requestAnimationFrame(fitToScreen);
  });

  stage.addEventListener('click', () => {
    selectedUid = null;
    applyTreeHighlight();
  });

  // Search Engine
  const searchInput = document.getElementById('searchInput');
  const searchResults = document.getElementById('searchResults');
  if (searchInput && searchResults) {
    function expandAncestors(node) {
      let p = node.parent;
      while (p) {
        p.expanded = true;
        p = p.parent;
      }
    }

    function goToNode(node) {
      expandAncestors(node);
      selectedUid = node.uid;
      renderCanvasTree();

      const r = stage.getBoundingClientRect();
      zoom = Math.max(zoom, 0.7);
      panX = r.width / 2  - node._x * zoom;
      panY = r.height / 2 - node._y * zoom;
      applyCanvasTransform();

      const el = nodeElPool.get(node.uid);
      if (el) {
        el.classList.add('found');
        setTimeout(() => el.classList.remove('found'), 2400);
      }
      searchResults.style.display = 'none';
      searchInput.blur();
      openMemberDetails(node.user_id || node.uid, node);
    }

    searchInput.addEventListener('input', () => {
      const q = searchInput.value.trim().toLowerCase();
      if (q.length < 1) { searchResults.style.display = 'none'; return; }
      const matches = flatIndex.filter(n =>
        n.id.toLowerCase().includes(q) ||
        n.fullId.toLowerCase().includes(q) ||
        n.name.toLowerCase().includes(q) ||
        n.fullName.toLowerCase().includes(q)
      ).slice(0, 20);

      if (!matches.length) {
        searchResults.innerHTML = `<div style="opacity:.6;cursor:default">Hech narsa topilmadi</div>`;
        searchResults.style.display = 'block';
        return;
      }
      searchResults.innerHTML = matches.map(n =>
        `<div data-uid="${n.uid}"><span>${n.name}</span><span class="rid">${n.id} <span class="rlvl">· L${n.level}</span></span></div>`
      ).join('');
      searchResults.style.display = 'block';
    });

    searchResults.addEventListener('click', (e) => {
      const row = e.target.closest('div[data-uid]');
      if (!row) return;
      const node = flatIndex.find(n => n.uid === Number(row.dataset.uid));
      if (node) goToNode(node);
    });

    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = searchInput.value.trim().toLowerCase();
        const node = flatIndex.find(n => n.id.toLowerCase() === q || n.fullId.toLowerCase() === q) ||
                     flatIndex.find(n => n.name.toLowerCase().includes(q) || n.fullName.toLowerCase().includes(q));
        if (node) goToNode(node);
      }
    });

    document.addEventListener('click', (e) => {
      if (!e.target.closest('#searchWrap')) searchResults.style.display = 'none';
    });
  }
}

// 2. List View Node Renderer
function renderListTreeNode(node, isRoot = false) {
  const uid = node.user_id || node.uid || 0;
  const fullName = isRoot
    ? `👑 Siz (${node.fullName || node.first_name || ''})`.trim()
    : `${node.fullName || node.first_name || ''}`.trim() || 'Hamkor';

  const username = node.username ? `@${node.username}` : '';
  const lvl = node.level !== undefined ? node.level : (node.current_level || 0);
  const hasChildren = node.children && node.children.length > 0;
  const descCount = countTreeDescendants(node);

  const countBadge = hasChildren
    ? `<span class="tree-count-badge">👥 ${node.children.length}${descCount > node.children.length ? `+${descCount - node.children.length}` : ''}</span>`
    : '';

  const cardClass = isRoot ? 'tree-person-card root-card' : 'tree-person-card';
  const avatarIcon = isRoot ? '👑' : getUserLvlEmoji(lvl);

  let contactBtn = '';
  if (!isRoot && (node.username || node.user_id)) {
    const contactUrl = node.username ? `https://t.me/${node.username}` : `tg://user?id=${node.user_id}`;
    contactBtn = `<a href="${contactUrl}" target="_blank" class="tree-contact-btn" title="Telegramda yozish" onclick="event.stopPropagation();">💬</a>`;
  }

  const html = `
    <div class="tree-person">
      <div class="${cardClass}" onclick="openMemberDetails(${node.user_id || node.uid}, null)">
        <div class="tree-avatar">${avatarIcon}</div>
        <div class="tree-info">
          <div class="tree-name">${fullName} ${countBadge}</div>
          <div class="tree-meta">
            <code style="font-size:10.5px; color:#94a3b8;">${node.id ? `ID: ${node.id}` : ''}</code>
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

// Switch between Canvas Tree view and List view
function switchTreeView(mode) {
  currentTreeViewMode = mode;
  document.querySelectorAll('.struct-tab').forEach(b => b.classList.remove('active'));

  const activeBtn = document.getElementById(mode === 'chart' ? 'btn-view-chart' : 'btn-view-list');
  if (activeBtn) activeBtn.classList.add('active');

  const stage = document.getElementById('stage');
  const zoomCtrl = document.getElementById('zoomCtrl');
  const listContainer = document.getElementById('user-list-container');

  if (mode === 'chart') {
    if (stage) stage.style.display = 'block';
    if (zoomCtrl) zoomCtrl.style.display = 'flex';
    if (listContainer) listContainer.style.display = 'none';
    renderCanvasTree();
    fitToScreen();
  } else {
    if (stage) stage.style.display = 'none';
    if (zoomCtrl) zoomCtrl.style.display = 'none';
    if (listContainer) {
      listContainer.style.display = 'block';
      listContainer.innerHTML = canvasRoot ? renderListTreeNode(canvasRoot, true) : '';
    }
  }
}

// Open Member Details Modal
function openMemberDetails(uid, directNode = null) {
  const node = directNode || flatIndex.find(n => n.user_id === uid || n.uid === uid) || (window._treeNodeMap ? window._treeNodeMap[uid] : null);
  if (!node) return;

  const fullName = node.fullName || `${node.first_name || ''} ${node.last_name || ''}`.trim() || 'Hamkor';
  const uname = node.username ? `@${node.username}` : 'Mavjud emas';
  const lvl = node.level !== undefined ? node.level : (node.current_level || 0);
  const descCount = countTreeDescendants(node);
  const directCount = node.children ? node.children.length : 0;
  const rawId = node.fullId || node.user_id || node.id || '-';

  const nameEl = document.getElementById('m-modal-name');
  if (nameEl) nameEl.innerText = fullName;

  const handleEl = document.getElementById('m-modal-handle');
  if (handleEl) handleEl.innerText = uname;

  const idEl = document.getElementById('m-modal-id');
  if (idEl) idEl.innerText = rawId;

  const dateEl = document.getElementById('m-modal-date');
  if (dateEl) dateEl.innerText = node.registered_at ? String(node.registered_at).slice(0, 10) : '-';

  const lvlEl = document.getElementById('m-modal-level');
  if (lvlEl) lvlEl.innerText = `${lvl}-Daraja`;

  const refsEl = document.getElementById('m-modal-refs');
  if (refsEl) refsEl.innerText = `👥 ${directCount} ta to'g'ridan-to'g'ri (${descCount} jami)`;

  const avatarEl = document.getElementById('m-modal-avatar');
  if (avatarEl) avatarEl.innerText = getUserLvlEmoji(lvl);

  currentSelectedMemberNode = node;

  // Reset forms in modal
  const replaceForm = document.getElementById('form-tree-replace');
  const insertForm = document.getElementById('form-tree-insert');
  if (replaceForm) {
    replaceForm.style.display = 'none';
    const inp = document.getElementById('input-replace-target');
    if (inp) inp.value = '';
  }
  if (insertForm) {
    insertForm.style.display = 'none';
    const inp = document.getElementById('input-insert-target');
    if (inp) inp.value = '';
  }

  // Curator/Admin action box: Only display for authorized admins
  const curatorBox = document.getElementById('curator-actions-box');
  if (curatorBox) {
    curatorBox.style.display = userState.isAdmin ? 'flex' : 'none';
  }

  const chatBtn = document.getElementById('m-modal-chat-btn');
  if (chatBtn) {
    if (node.username) {
      chatBtn.href = `https://t.me/${node.username}`;
    } else if (node.user_id) {
      chatBtn.href = `tg://user?id=${node.user_id}`;
    } else {
      chatBtn.href = '#';
    }
  }

  const modal = document.getElementById('member-detail-modal');
  if (modal) modal.style.display = 'flex';
}

let currentSelectedMemberNode = null;

function toggleTreeActionForm(type) {
  const replaceForm = document.getElementById('form-tree-replace');
  const insertForm = document.getElementById('form-tree-insert');

  if (type === 'replace') {
    if (replaceForm && replaceForm.style.display === 'block') {
      replaceForm.style.display = 'none';
    } else if (replaceForm) {
      replaceForm.style.display = 'block';
      if (insertForm) insertForm.style.display = 'none';
      document.getElementById('input-replace-target')?.focus();
    }
  } else if (type === 'insert') {
    if (insertForm && insertForm.style.display === 'block') {
      insertForm.style.display = 'none';
    } else if (insertForm) {
      insertForm.style.display = 'block';
      if (replaceForm) replaceForm.style.display = 'none';
      document.getElementById('input-insert-target')?.focus();
    }
  }
}

function submitTreeReplace() {
  if (!currentSelectedMemberNode) return;
  const targetUid = currentSelectedMemberNode.user_id;
  const inputEl = document.getElementById('input-replace-target');
  const val = inputEl ? inputEl.value.trim() : '';

  if (!val) {
    showToast("⚠️ Yangi hamkor username yoki ID sini kiriting");
    return;
  }

  showToast("⏳ Almashtirilmoqda...");
  fetch('/api/user/tree/replace', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_user_id: targetUid,
      new_identifier: val,
      requester_id: userState.id || targetUid
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast("✅ " + (data.message || "Muvaffaqiyatli almashtirildi!"));
      closeModal('member-detail-modal');
      loadUserTree();
    } else {
      showToast("❌ Xatolik: " + (data.error || "Almashtirib bo'lmadi"));
    }
  })
  .catch(err => {
    showToast("❌ Server xatoligi yuz berdi");
  });
}

function submitTreeInsert() {
  if (!currentSelectedMemberNode) return;
  const targetUid = currentSelectedMemberNode.user_id;
  const inputEl = document.getElementById('input-insert-target');
  const val = inputEl ? inputEl.value.trim() : '';
  const modeEl = document.querySelector('input[name="insert-mode"]:checked');
  const mode = modeEl ? modeEl.value : 'above';

  if (!val) {
    showToast("⚠️ Yangi a'zo username yoki ID sini kiriting");
    return;
  }

  showToast("⏳ Zanjirga qo'shilmoqda...");
  fetch('/api/user/tree/insert', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_user_id: targetUid,
      new_identifier: val,
      mode: mode,
      requester_id: userState.id || targetUid
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast("✅ " + (data.message || "Muvaffaqiyatli qo'shildi!"));
      closeModal('member-detail-modal');
      loadUserTree();
    } else {
      showToast("❌ Xatolik: " + (data.error || "Qo'shib bo'lmadi"));
    }
  })
  .catch(err => {
    showToast("❌ Server xatoligi yuz berdi");
  });
}

function closeMemberModal(e) {
  const modal = document.getElementById('member-detail-modal');
  if (modal) modal.style.display = 'none';
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.style.display = 'none';
}

// Load Tree Data from Database API
function loadUserTree(retryCount) {
  const loadingOverlay = document.getElementById('canvas-loading-overlay');
  if (loadingOverlay) loadingOverlay.style.display = 'none';

  detectTelegramUser();
  const targetUid = userState.id || 0;

  fetch(`/api/user/tree?user_id=${targetUid}`)
    .then(res => res.json())
    .then(d => {
      if (d.is_admin !== undefined) {
        userState.isAdmin = Boolean(d.is_admin);
      }

      let apiTree = (d.success && d.tree) ? d.tree : null;
      if (!apiTree) {
        apiTree = {
          user_id: userState.id || 10475,
          first_name: userState.first_name || 'Siz',
          last_name: userState.last_name || '',
          username: userState.username || '',
          current_level: userState.level || 0,
          children: []
        };
      }

      currentTreeData = apiTree;
      flatIndex = [];
      nodeElPool.clear();
      const viewport = document.getElementById('viewport');
      if (viewport) {
        Array.from(viewport.querySelectorAll('.node')).forEach(el => el.remove());
      }

      canvasRoot = buildCanvasTree(apiTree, 0, null);

      // Stats Update
      const totalDesc = countTreeDescendants(apiTree);
      const l1Count = apiTree.children ? apiTree.children.length : 0;
      let l2Count = 0;
      if (apiTree.children) {
        apiTree.children.forEach(c => {
          if (c.children) l2Count += c.children.length;
        });
      }

      const totalEl = document.getElementById("tree-stat-total");
      if (totalEl) totalEl.innerText = totalDesc;

      const l1El = document.getElementById("tree-stat-l1");
      if (l1El) l1El.innerText = `${l1Count}/3`;

      const l2El = document.getElementById("tree-stat-l2");
      if (l2El) l2El.innerText = `${l2Count}/9`;

      const lvlEl = document.getElementById("tree-stat-level");
      if (lvlEl) lvlEl.innerText = `${apiTree.current_level !== undefined ? apiTree.current_level : (userState.level || 0)}`;

      attachCanvasListeners();
      renderCanvasTree();
      setTimeout(fitToScreen, 50);
    })
    .catch(err => {
      console.error("Tree loading error:", err);
      attachCanvasListeners();
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
