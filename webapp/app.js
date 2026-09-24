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

// ==========================================
// MULTI-ACCOUNT STORAGE & HELPERS
// ==========================================
function getSavedAccounts() {
  try {
    const raw = localStorage.getItem('bh_saved_accounts');
    if (raw) {
      const list = JSON.parse(raw);
      if (Array.isArray(list)) return list;
    }
  } catch (e) {}
  return [];
}

function saveAccountsList(list) {
  try {
    localStorage.setItem('bh_saved_accounts', JSON.stringify(list));
  } catch (e) {}
}

function ensureAccountInSaved(acc) {
  if (!acc || !acc.id) return;
  const list = getSavedAccounts();
  const idx = list.findIndex(a => Number(a.id) === Number(acc.id));
  const fullAcc = {
    id: Number(acc.id),
    first_name: acc.first_name || 'Foydalanuvchi',
    last_name: acc.last_name || '',
    username: acc.username || '',
    level: acc.level !== undefined ? acc.level : (acc.current_level || 1),
    balance: acc.balance || 0,
    total_earned: acc.total_earned || acc.income || 0,
    is_primary: acc.is_primary !== undefined ? acc.is_primary : (idx >= 0 ? Boolean(list[idx].is_primary) : false)
  };

  if (idx >= 0) {
    list[idx] = { ...list[idx], ...fullAcc };
  } else {
    list.push(fullAcc);
  }
  saveAccountsList(list);
  return fullAcc;
}

// Robust user extraction from Telegram WebApp, URL params, hash, or local cache
function detectTelegramUser() {
  let detectedTgId = 0;
  let detectedUser = null;

  // 1. Direct Telegram WebApp user object
  if (tg?.initDataUnsafe?.user?.id) {
    const u = tg.initDataUnsafe.user;
    detectedTgId = Number(u.id);
    detectedUser = {
      id: detectedTgId,
      first_name: u.first_name || "Foydalanuvchi",
      last_name: u.last_name || "",
      username: u.username || "",
      is_primary: true
    };
  }

  // 2. Query parameters (?user_id=123 or ?uid=123 or ?tgWebAppStartParam=123)
  const urlParams = new URLSearchParams(window.location.search);
  const qId = urlParams.get('user_id') || urlParams.get('uid') || urlParams.get('tgWebAppStartParam');
  if (qId && !isNaN(qId) && Number(qId) > 0) {
    if (!detectedTgId) {
      detectedTgId = Number(qId);
      detectedUser = { id: detectedTgId, first_name: "Foydalanuvchi", last_name: "", username: "", is_primary: true };
    }
  }

  // 3. Raw Telegram initData string parser
  if (!detectedTgId && tg?.initData) {
    try {
      const parsed = new URLSearchParams(tg.initData);
      const userRaw = parsed.get('user');
      if (userRaw) {
        const uObj = JSON.parse(userRaw);
        if (uObj.id) {
          detectedTgId = Number(uObj.id);
          detectedUser = {
            id: detectedTgId,
            first_name: uObj.first_name || "Foydalanuvchi",
            last_name: uObj.last_name || "",
            username: uObj.username || "",
            is_primary: true
          };
        }
      }
    } catch(e) {}
  }

  // 4. Hash parameters parser (e.g. #tgWebAppData=...)
  if (!detectedTgId && window.location.hash) {
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
            detectedTgId = Number(uObj.id);
            detectedUser = {
              id: detectedTgId,
              first_name: uObj.first_name || "Foydalanuvchi",
              last_name: uObj.last_name || "",
              username: uObj.username || "",
              is_primary: true
            };
          }
        }
      }
    } catch(e) {}
  }

  // Record primary Telegram account in saved accounts
  if (detectedTgId && detectedUser) {
    const primaryStored = localStorage.getItem('bh_primary_account_id');
    if (!primaryStored) {
      localStorage.setItem('bh_primary_account_id', String(detectedTgId));
    }
    ensureAccountInSaved(detectedUser);
  }

  // 5. Active account resolution: prioritize user-selected active account
  const activeStoredId = localStorage.getItem('bh_active_account_id');
  if (activeStoredId && !isNaN(activeStoredId) && Number(activeStoredId) > 0) {
    userState.id = Number(activeStoredId);
  } else if (detectedTgId) {
    userState.id = detectedTgId;
    localStorage.setItem('bh_active_account_id', String(userState.id));
  } else {
    const saved = sessionStorage.getItem('bh_user_id') || localStorage.getItem('bh_user_id');
    if (saved && !isNaN(saved) && Number(saved) > 0) {
      userState.id = Number(saved);
    }
  }

  // Populate local info from cache if available
  const list = getSavedAccounts();
  const matchedAcc = list.find(a => Number(a.id) === Number(userState.id));
  if (matchedAcc) {
    userState.first_name = matchedAcc.first_name || userState.first_name;
    userState.last_name = matchedAcc.last_name || "";
    userState.username = matchedAcc.username || "";
    if (matchedAcc.level) userState.level = matchedAcc.level;
  } else if (detectedUser && Number(userState.id) === detectedTgId) {
    userState.first_name = detectedUser.first_name || userState.first_name;
    userState.last_name = detectedUser.last_name || "";
    userState.username = detectedUser.username || "";
  }

  if (userState.id) {
    try {
      sessionStorage.setItem('bh_user_id', String(userState.id));
      localStorage.setItem('bh_user_id', String(userState.id));
    } catch (e) {}
  }
}

// ==========================================
// MULTI-ACCOUNT MODAL & SWITCH ACTIONS
// ==========================================
function openAccountsModal() {
  renderAccountsList();
  const form = document.getElementById('form-add-account');
  if (form) form.style.display = 'none';
  const inp = document.getElementById('input-new-account-id');
  if (inp) inp.value = '';
  const modal = document.getElementById('accounts-modal');
  if (modal) modal.style.display = 'flex';
}

function renderAccountsList() {
  const container = document.getElementById('accounts-list-container');
  if (!container) return;

  const accounts = getSavedAccounts();
  // Ensure current user is in list
  if (userState.id && !accounts.some(a => Number(a.id) === Number(userState.id))) {
    ensureAccountInSaved({
      id: userState.id,
      first_name: userState.first_name,
      last_name: userState.last_name,
      username: userState.username,
      level: userState.level,
      total_earned: userState.income,
      is_primary: true
    });
  }

  const updatedList = getSavedAccounts();

  if (!updatedList.length) {
    container.innerHTML = `
      <div style="text-align:center; padding:18px; color:#94a3b8; font-size:12.5px;">
        Saqlangan akkauntlar topilmadi.
      </div>
    `;
    return;
  }

  let html = '';
  updatedList.forEach(acc => {
    const isActive = Number(acc.id) === Number(userState.id);
    const fullName = `${acc.first_name || ''} ${acc.last_name || ''}`.trim() || 'Foydalanuvchi';
    const uname = acc.username ? `@${acc.username}` : `ID: ${acc.id}`;
    const initial = (acc.first_name ? acc.first_name.charAt(0) : 'U').toUpperCase();
    const lvlEmoji = getUserLvlEmoji ? getUserLvlEmoji(acc.level || 1) : '🌱';

    html += `
      <div style="background:${isActive ? 'linear-gradient(135deg, rgba(34,197,94,0.18), rgba(234,179,8,0.15))' : 'rgba(255,255,255,0.04)'}; border:1px solid ${isActive ? '#22c55e' : 'rgba(255,255,255,0.12)'}; border-radius:14px; padding:12px; display:flex; align-items:center; justify-content:space-between; gap:10px; transition:all 0.2s ease;">
        <div style="display:flex; align-items:center; gap:10px; flex:1; min-width:0;">
          <div style="width:38px; height:38px; border-radius:50%; background:${isActive ? '#22c55e' : '#334155'}; color:${isActive ? '#000' : '#fff'}; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:15px; flex-shrink:0;">
            ${initial}
          </div>
          <div style="flex:1; min-width:0;">
            <div style="display:flex; align-items:center; gap:6px;">
              <span style="font-weight:800; font-size:13.5px; color:#fff; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:140px;">${fullName}</span>
              ${isActive ? `<span style="font-size:10px; background:#22c55e; color:#000; font-weight:800; padding:1px 6px; border-radius:10px;">FAOL</span>` : ''}
              ${acc.is_primary ? `<span style="font-size:9.5px; background:rgba(56,189,248,0.2); color:#38bdf8; font-weight:700; padding:1px 5px; border-radius:6px;" title="Asosiy Telegram Akkaunt">Asosiy</span>` : ''}
            </div>
            <div style="font-size:11px; color:#94a3b8; display:flex; align-items:center; gap:6px; margin-top:2px;">
              <span>${uname}</span>
              <span>•</span>
              <span style="color:#facc15; font-weight:700;">${lvlEmoji} ${acc.level || 1}-daraja</span>
            </div>
          </div>
        </div>

        <div style="display:flex; align-items:center; gap:6px; flex-shrink:0;">
          ${isActive ? `
            <div style="font-size:11px; color:#86efac; font-weight:800; display:flex; align-items:center; gap:3px; padding:6px 10px; background:rgba(34,197,94,0.15); border-radius:10px;">
              <span>✓ Joriy</span>
            </div>
          ` : `
            <button type="button" onclick="confirmSwitchToAccount(${acc.id})" style="padding:6px 12px; background:linear-gradient(135deg, #eab308, #ca8a04); border:none; color:#000; border-radius:10px; font-weight:800; font-size:11.5px; cursor:pointer; display:flex; align-items:center; gap:4px;">
              <span>O'tish</span>
              <span>➡️</span>
            </button>
          `}
          ${!isActive && !acc.is_primary ? `
            <button type="button" onclick="removeSavedAccount(${acc.id})" style="background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); color:#ef4444; border-radius:8px; width:28px; height:28px; cursor:pointer; display:flex; align-items:center; justify-content:center; font-size:13px;" title="Akkauntni ro'yxatdan o'chirish">
              🗑️
            </button>
          ` : ''}
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function toggleAddAccountForm() {
  const form = document.getElementById('form-add-account');
  if (!form) return;
  const isHidden = form.style.display === 'none' || !form.style.display;
  form.style.display = isHidden ? 'block' : 'none';
  if (isHidden) {
    const input = document.getElementById('input-new-account-id');
    if (input) {
      input.value = '';
      input.focus();
    }
  }
}

function submitAddNewAccount() {
  const input = document.getElementById('input-new-account-id');
  const query = input ? input.value.trim() : '';

  if (!query) {
    showToast("⚠️ Telegram username yoki ID raqamini kiriting");
    return;
  }

  showToast("🔍 Akkaunt qidirilmoqda...");

  fetch(`/api/user/lookup?query=${encodeURIComponent(query)}`)
    .then(res => res.json())
    .then(data => {
      if (data.success && data.user) {
        const u = data.user;
        ensureAccountInSaved({
          id: u.user_id,
          first_name: u.first_name,
          last_name: u.last_name,
          username: u.username,
          level: u.current_level,
          balance: u.balance,
          total_earned: u.total_earned,
          is_primary: false
        });

        showToast(`✅ Akkaunt qo'shildi: ${u.first_name || u.username || u.user_id}`);
        toggleAddAccountForm();
        renderAccountsList();

        // Prompt switch immediately
        confirmSwitchToAccount(u.user_id);
      } else {
        showToast("❌ " + (data.error || "Foydalanuvchi topilmadi"));
      }
    })
    .catch(err => {
      console.error(err);
      showToast("❌ Server xatoligi yuz berdi");
    });
}

function confirmSwitchToAccount(targetAccId) {
  const targetId = Number(targetAccId);
  if (!targetId) return;

  if (targetId === Number(userState.id)) {
    showToast("ℹ️ Bu akkaunt allaqachon faol!");
    return;
  }

  const list = getSavedAccounts();
  const acc = list.find(a => Number(a.id) === targetId) || { id: targetId, first_name: `ID ${targetId}` };
  const accName = `${acc.first_name || ''} ${acc.last_name || ''}`.trim() || acc.username || `ID ${acc.id}`;
  const unameOrId = acc.username ? `@${acc.username}` : `ID: ${acc.id}`;

  const descEl = document.getElementById('switch-confirm-desc');
  if (descEl) {
    descEl.innerHTML = `Siz <b>${accName}</b> (<span style="color:#38bdf8;">${unameOrId}</span>) akkauntingizga o'tmoqdasiz.`;
  }

  const confirmBtn = document.getElementById('btn-confirm-account-switch');
  if (confirmBtn) {
    confirmBtn.onclick = () => executeAccountSwitch(targetId);
  }

  const confirmModal = document.getElementById('account-switch-confirm-modal');
  if (confirmModal) confirmModal.style.display = 'flex';
}

function executeAccountSwitch(targetAccId) {
  const targetId = Number(targetAccId);
  if (!targetId) return;

  try {
    localStorage.setItem('bh_active_account_id', String(targetId));
    sessionStorage.setItem('bh_user_id', String(targetId));
    localStorage.setItem('bh_user_id', String(targetId));
  } catch (e) {}

  closeModal('account-switch-confirm-modal');
  closeModal('accounts-modal');

  const list = getSavedAccounts();
  const acc = list.find(a => Number(a.id) === targetId);
  const accName = acc ? (`${acc.first_name || ''} ${acc.last_name || ''}`.trim() || acc.username || `ID: ${acc.id}`) : `ID: ${targetId}`;

  // Show fullscreen feedback overlay
  let switchScreen = document.getElementById('switch-success-screen');
  if (!switchScreen) {
    switchScreen = document.createElement('div');
    switchScreen.id = 'switch-success-screen';
    switchScreen.style.position = 'fixed';
    switchScreen.style.top = '0';
    switchScreen.style.left = '0';
    switchScreen.style.right = '0';
    switchScreen.style.bottom = '0';
    switchScreen.style.zIndex = '99999';
    switchScreen.style.background = 'radial-gradient(circle at center, #0c2016 0%, #050b08 100%)';
    switchScreen.style.display = 'flex';
    switchScreen.style.flexDirection = 'column';
    switchScreen.style.alignItems = 'center';
    switchScreen.style.justifyContent = 'center';
    switchScreen.style.padding = '24px';
    switchScreen.style.textAlign = 'center';
    switchScreen.style.color = '#fff';
    switchScreen.style.fontFamily = 'sans-serif';
    document.body.appendChild(switchScreen);
  }

  switchScreen.innerHTML = `
    <div style="width:72px; height:72px; border-radius:50%; background:rgba(34,197,94,0.2); border:2px solid #22c55e; display:flex; align-items:center; justify-content:center; font-size:36px; margin-bottom:16px;">
      🔄
    </div>
    <h2 style="font-size:20px; font-weight:800; color:#facc15; margin-bottom:8px;">Akkaunt almashtirildi!</h2>
    <p style="font-size:14px; color:#cbd5e1; max-width:320px; line-height:1.45; margin-bottom:14px;">
      Siz muvaffaqiyatli <b>${accName}</b> akkauntiga o'tdingiz.
    </p>
    <div style="font-size:12px; color:#94a3b8; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1); padding:10px 14px; border-radius:12px; max-width:320px; margin-bottom:22px; line-height:1.4; text-align:center;">
      💡 Botdan Mini Appni qayta ochganingizda ushbu yangi akkaunt bilan to'liq ochiladi.
    </div>
    <button id="btn-close-webapp-now" style="background:linear-gradient(135deg, #eab308, #ca8a04); border:none; color:#000; font-weight:800; font-size:14px; padding:12px 28px; border-radius:12px; cursor:pointer; box-shadow:0 4px 15px rgba(234,179,8,0.4);">
      Ilovani Yopish
    </button>
  `;

  const btnClose = document.getElementById('btn-close-webapp-now');
  if (btnClose) {
    btnClose.onclick = () => {
      if (tg && tg.close) {
        try { tg.close(); } catch(e) {}
      } else {
        window.location.reload();
      }
    };
  }

  // Attempt auto-close in Telegram WebApp context
  setTimeout(() => {
    if (tg && tg.close) {
      try {
        tg.close();
      } catch (e) {
        console.warn("Could not auto-close WebApp:", e);
      }
    }
  }, 400);
}

function removeSavedAccount(accId) {
  const targetId = Number(accId);
  if (!targetId) return;

  if (targetId === Number(userState.id)) {
    showToast("⚠️ Hozirgi faol akkauntni o'chirib bo'lmaydi");
    return;
  }

  const list = getSavedAccounts().filter(a => Number(a.id) !== targetId);
  saveAccountsList(list);
  showToast("🗑️ Akkaunt ro'yxatdan olib tashlandi");
  renderAccountsList();
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

  const unameParam = encodeURIComponent(userState.username || '');
  const fnParam = encodeURIComponent(userState.first_name || '');
  const lnParam = encodeURIComponent(userState.last_name || '');
  fetch(`/api/user/profile?user_id=${userState.id}&username=${unameParam}&first_name=${fnParam}&last_name=${lnParam}`)
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

        // Sync to saved accounts
        ensureAccountInSaved({
          id: userState.id,
          first_name: userState.first_name,
          last_name: userState.last_name,
          username: userState.username,
          level: userState.level,
          balance: u.balance || 0,
          total_earned: userState.income
        });

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
    // Small delay ensures the section is visible (has width/height) before loading tree
    setTimeout(() => loadUserTree(), 80);
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
const ZOOM_MIN         = 0.35;
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
  if (level === 0) {
    flatIndex = [];
  }
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
    expanded: level < 2 // Expand root and 1st level by default for clean presentation
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
    const totalD = countTreeDescendants(node);
    badge.textContent = totalD > node.children.length ? `${node.children.length}+${totalD - node.children.length}` : node.children.length;
    badge.title = `${totalD} ta jamoa a'zosi`;
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
  if (!stage || !contentW || !canvasRoot) return;
  const r = stage.getBoundingClientRect();
  const width = (r.width > 0 ? r.width : (stage.clientWidth || stage.offsetWidth || window.innerWidth || 360));
  const height = (r.height > 0 ? r.height : (stage.clientHeight || stage.offsetHeight || 500));
  const pad = 30;
  const scaleX = (width - pad * 2) / Math.max(contentW, 1);
  const scaleY = (height - pad * 2) / Math.max(contentH, 200);
  
  zoom = Math.min(1.1, Math.max(ZOOM_MIN, Math.min(scaleX, scaleY)));
  const rootX = canvasRoot._x || (contentW / 2);
  panX = (width / 2) - (rootX * zoom);
  panY = 28;
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

  // 1. Kurator (Tepasidagi a'zo) display
  const curatorEl = document.getElementById('m-modal-curator');
  if (curatorEl) {
    if (node.parent) {
      const pUname = node.parent.username ? `@${node.parent.username}` : '';
      const pName = node.parent.fullName || node.parent.name || 'Kurator';
      const pId = node.parent.fullId || node.parent.id || '';
      curatorEl.innerHTML = `${pName} ${pUname ? `<span style="color:#38bdf8;">(${pUname})</span>` : ''} <code style="font-size:10px; color:#cbd5e1;">[ID: ${pId}]</code>`;
    } else if (node.treeDepth === 0) {
      curatorEl.innerHTML = `<span style="color:#22c55e;">👑 Bosh Admin (Tizim)</span>`;
    } else if (node.referrer_id) {
      const pNode = flatIndex.find(n => n.user_id === node.referrer_id || n.id === String(node.referrer_id));
      if (pNode) {
        const pUname = pNode.username ? `@${pNode.username}` : '';
        const pName = pNode.fullName || pNode.name || 'Kurator';
        curatorEl.innerHTML = `${pName} ${pUname ? `<span style="color:#38bdf8;">(${pUname})</span>` : ''} <code style="font-size:10px; color:#cbd5e1;">[ID: ${pNode.fullId || pNode.id}]</code>`;
      } else {
        curatorEl.innerHTML = `Kurator ID: <code>${node.referrer_id}</code>`;
      }
    } else {
      curatorEl.innerHTML = `<span style="color:#22c55e;">👑 Bosh Admin (Tizim)</span>`;
    }
  }

  // 2. Quyi a'zolari (Bolalari) display
  const childrenListEl = document.getElementById('m-modal-children-list');
  const parentRefId = node.referrer_id || (node.parent ? (node.parent.user_id || node.parent.id) : 0);
  if (childrenListEl) {
    if (node.children && node.children.length > 0) {
      const itemsHtml = node.children.map((ch, idx) => {
        const chName = ch.fullName || ch.name || 'Hamkor';
        const chUname = ch.username ? `@${ch.username}` : '';
        const chId = ch.user_id || ch.fullId || ch.id || '';
        const chLvl = ch.level !== undefined ? ch.level : (ch.current_level || 1);
        const canMoveUp = userState.isAdmin && parentRefId && parentRefId != 0;
        return `
          <div style="display:flex; align-items:center; justify-content:space-between; padding:4px 0; border-bottom:1px dashed rgba(255,255,255,0.08);">
            <div style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding-right:4px;">
              <span style="color:#f2b33d; font-weight:700;">${idx + 1}.</span> <b>${chName}</b>
              ${chUname ? `<span style="color:#38bdf8; font-size:11px;">(${chUname})</span>` : ''}
              <code style="font-size:10px; color:#94a3b8; margin-left:3px;">[ID: ${chId}]</code>
            </div>
            <div style="display:flex; align-items:center; gap:4px;">
              <span style="font-size:10px; background:rgba(34,197,94,0.2); color:#86efac; padding:1px 5px; border-radius:5px; font-weight:700;">${chLvl}-daraja</span>
              ${canMoveUp ? `
                <button type="button" onclick="moveChildToParent(${ch.user_id || chId}, ${parentRefId}, '${chName.replace(/'/g, "\\'")}')" style="background:rgba(56,189,248,0.2); border:1px solid #38bdf8; color:#38bdf8; border-radius:6px; font-size:10.5px; padding:2px 6px; cursor:pointer; font-weight:700; white-space:nowrap;" title="Ushbu a'zoni ${node.name} dan chiqarib, to'g'ridan-to'g'ri Kuratoriga o'tkazish">
                  ⬆️ Kuratorga
                </button>
              ` : ''}
            </div>
          </div>
        `;
      }).join('');
      childrenListEl.innerHTML = itemsHtml;
    } else {
      childrenListEl.innerHTML = `<span style="color:#94a3b8; font-style:italic;">Bevosita quyi hamkorlar yo'q (0 ta)</span>`;
    }
  }

  currentSelectedMemberNode = node;

  // Reset all 5 forms in modal
  ['form-tree-replace', 'form-tree-move', 'form-tree-transfer', 'form-tree-remove', 'form-tree-insert'].forEach(id => {
    const f = document.getElementById(id);
    if (f) f.style.display = 'none';
  });
  const inpR = document.getElementById('input-replace-target');
  if (inpR) inpR.value = '';
  const inpM = document.getElementById('input-move-curator');
  if (inpM) inpM.value = '';
  const inpT = document.getElementById('input-transfer-from');
  if (inpT) inpT.value = '';
  const inpI = document.getElementById('input-insert-target');
  if (inpI) inpI.value = '';

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

function moveChildToParent(childId, defaultParentId, childName) {
  if (!childId) {
    showToast("⚠️ Foydalanuvchi ID si topilmadi");
    return;
  }
  
  const targetCuratorInput = prompt(
    `🔄 ${childName || 'Ushbu a\'zo'}ni QAYSI Kuratorga ulamoqchisiz?\n\nYangi Kurator Telegram ID raqami yoki @username ini kiriting:`,
    defaultParentId && defaultParentId != 0 ? defaultParentId : ''
  );

  if (targetCuratorInput === null) return; // Bekor qilindi
  const curatorVal = targetCuratorInput.trim();
  if (!curatorVal) {
    showToast("⚠️ Yangi Kurator ID yoki username kiritilmadi!");
    return;
  }

  doMoveUserApi(childId, curatorVal, false);
}

function doMoveUserApi(targetUid, curatorVal, force = false) {
  showToast("⏳ Kuratorga o'tkazilmoqda...");
  fetch('/api/user/tree/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_user_id: Number(targetUid),
      new_curator_identifier: String(curatorVal),
      requester_id: userState.id || 0,
      force: force
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast("✅ " + (data.message || "Muvaffaqiyatli o'tkazildi!"));
      closeModal('member-detail-modal');
      loadUserTree();
    } else if (data.is_full) {
      if (confirm(`${data.error}\n\nBaribir ushbu kuratorga majburiy qo'shishni tasdiqlaysizmi?`)) {
        doMoveUserApi(targetUid, curatorVal, true);
      }
    } else {
      showToast("❌ Xatolik: " + (data.error || "O'tkazib bo'lmadi"));
    }
  })
  .catch(err => {
    showToast("❌ Server xatoligi yuz berdi");
  });
}

let currentSelectedMemberNode = null;

function toggleTreeActionForm(type) {
  const formMap = {
    replace: 'form-tree-replace',
    move: 'form-tree-move',
    transfer: 'form-tree-transfer',
    remove: 'form-tree-remove',
    insert: 'form-tree-insert'
  };

  const targetFormId = formMap[type];
  const targetForm = document.getElementById(targetFormId);
  const isCurrentlyOpen = targetForm && targetForm.style.display === 'block';

  // Hide all
  Object.values(formMap).forEach(id => {
    const f = document.getElementById(id);
    if (f) f.style.display = 'none';
  });

  if (!isCurrentlyOpen && targetForm) {
    targetForm.style.display = 'block';
    if (type === 'replace') document.getElementById('input-replace-target')?.focus();
    if (type === 'move') document.getElementById('input-move-curator')?.focus();
    if (type === 'transfer') document.getElementById('input-transfer-from')?.focus();
    if (type === 'insert') document.getElementById('input-insert-target')?.focus();
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

function submitTreeMove() {
  if (!currentSelectedMemberNode) return;
  const targetUid = currentSelectedMemberNode.user_id;
  const inputEl = document.getElementById('input-move-curator');
  const val = inputEl ? inputEl.value.trim() : '';

  if (!val) {
    showToast("⚠️ Yangi Kurator username yoki ID sini kiriting");
    return;
  }

  doMoveUserApi(targetUid, val, false);
}

function submitTreeTransfer() {
  if (!currentSelectedMemberNode) return;
  const targetUid = currentSelectedMemberNode.user_id;
  const inputEl = document.getElementById('input-transfer-from');
  const val = inputEl ? inputEl.value.trim() : '';

  if (!val) {
    showToast("⚠️ Eski a'zo username yoki ID sini kiriting");
    return;
  }

  showToast("⏳ Referallar biriktirilmoqda...");
  fetch('/api/user/tree/transfer_referrals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from_identifier: val,
      to_identifier: String(targetUid),
      requester_id: userState.id || targetUid
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast("✅ " + (data.message || "Referallar muvaffaqiyatli biriktirildi!"));
      closeModal('member-detail-modal');
      loadUserTree();
    } else {
      showToast("❌ Xatolik: " + (data.error || "Referallarni biriktirib bo'lmadi"));
    }
  })
  .catch(err => {
    showToast("❌ Server xatoligi yuz berdi");
  });
}

function submitTreeRemove() {
  if (!currentSelectedMemberNode) return;
  const targetUid = currentSelectedMemberNode.user_id;
  const targetName = currentSelectedMemberNode.fullName || currentSelectedMemberNode.name || targetUid;

  if (!confirm(`Haqiqatan ham ${targetName} ni zanjir orasidan chiqarib, uning bolalarini to'g'ridan-to'g'ri kuratoriga ulamoqchimisiz?`)) {
    return;
  }

  showToast("⏳ Zanjirdan chiqarilmoqda...");
  fetch('/api/user/tree/remove', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_user_id: targetUid,
      requester_id: userState.id || targetUid
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast("✅ " + (data.message || "Zanjirdan muvaffaqiyatli chiqarildi!"));
      closeModal('member-detail-modal');
      loadUserTree();
    } else {
      showToast("❌ Xatolik: " + (data.error || "Zanjirdan chiqarib bo'lmadi"));
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

  const fallbackTree = {
    user_id: userState.id || 10475,
    first_name: userState.first_name || 'Siz',
    last_name: userState.last_name || '',
    username: userState.username || '',
    current_level: userState.level || 0,
    children: []
  };

  // Immediate default render if no canvasRoot yet
  if (!canvasRoot) {
    canvasRoot = buildCanvasTree(fallbackTree, 0, null);
    attachCanvasListeners();
    renderCanvasTree();
    fitToScreen();
  }

  const unameParam = encodeURIComponent(userState.username || '');
  fetch(`/api/user/tree?user_id=${targetUid}&username=${unameParam}`)
    .then(res => res.json())
    .then(d => {
      if (d.is_admin !== undefined) {
        userState.isAdmin = Boolean(d.is_admin);
      }

      if (!d.success || !d.tree) {
        console.warn("Tree API response:", d);
        return;
      }

      const apiTree = d.tree;
      currentTreeData = apiTree;

      const viewport = document.getElementById('viewport');
      if (viewport) {
        Array.from(viewport.querySelectorAll('.node')).forEach(el => el.remove());
      }
      nodeElPool.clear();
      flatIndex = [];

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
      fitToScreen();
    })
    .catch(err => {
      console.error("Tree loading error:", err);
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
