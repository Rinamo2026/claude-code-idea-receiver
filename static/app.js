/* Idea Receiver — Frontend (Server-synced Draft System) */
const API = window.__BASE_PATH || '';
let ws = null;

// --- DOM ---
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const authScreen = $('#auth-screen');
const mainScreen = $('#main-screen');
const inputSection = $('#input-section');
const historySection = $('#history-section');
const ideaText = $('#idea-text');
const submitStatus = $('#submit-status');
const progressBar = $('#progress-bar');
const slotList = $('#slot-list');

// --- Slot Management (localStorage + Server Sync) ---
const SLOTS_KEY = 'idea-receiver-slots';
const ACTIVE_KEY = 'idea-receiver-active-slot';
const SYNC_STATUS_KEY = 'idea-receiver-sync-ts';

let syncInFlight = false;
let syncTimer = null;
let changeCounter = 0;    // 変更ごとにインクリメント
let syncedCounter = 0;    // 同期成功時にchangeCounterの値をコピー
let syncError = null;     // null | 'auth' | 'network'

function loadSlots() {
  try {
    const raw = localStorage.getItem(SLOTS_KEY);
    if (raw) {
      const slots = JSON.parse(raw);
      if (Array.isArray(slots) && slots.length > 0) return slots;
    }
  } catch {}
  return [{ id: genSlotId(), text: '', label: '1' }];
}

function saveSlots(slots) {
  localStorage.setItem(SLOTS_KEY, JSON.stringify(slots));
}

function getActiveSlotId() {
  return localStorage.getItem(ACTIVE_KEY) || null;
}

function setActiveSlotId(id) {
  localStorage.setItem(ACTIVE_KEY, id);
}

function genSlotId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

let slots = loadSlots();
let activeSlotId = getActiveSlotId();

// Ensure activeSlotId is valid
if (!slots.find(s => s.id === activeSlotId)) {
  activeSlotId = slots[0].id;
  setActiveSlotId(activeSlotId);
}

function getActiveSlot() {
  return slots.find(s => s.id === activeSlotId);
}

function renderSlotList() {
  const fragment = document.createDocumentFragment();

  slots.forEach((s, i) => {
    const isActive = s.id === activeSlotId;
    const card = document.createElement('div');
    card.className = `slot-card${isActive ? ' slot-card-active' : ''}`;
    card.dataset.slotId = s.id;

    if (isActive) {
      // Active card: header + textarea (moved in)
      const header = document.createElement('div');
      header.className = 'slot-card-header';
      const label = document.createElement('span');
      label.className = 'slot-card-label';
      label.textContent = '編集中';
      header.appendChild(label);
      card.appendChild(header);

      // Physically move the existing textarea into this card
      card.appendChild(ideaText);
    } else {
      // Collapsed card: preview text
      const hasText = s.text.trim().length > 0;
      const preview = document.createElement('span');
      preview.className = 'slot-card-preview' + (hasText ? '' : ' slot-card-empty');
      preview.textContent = hasText ? s.text.trim().slice(0, 80) : '(空)';
      card.appendChild(preview);

      card.addEventListener('click', (e) => {
        if (e.target.closest('.slot-card-close')) return;
        switchSlot(s.id);
      });
    }

    // Close button (hidden when only 1 slot)
    if (slots.length > 1) {
      const closeBtn = document.createElement('button');
      closeBtn.className = 'slot-card-close';
      closeBtn.title = '削除';
      closeBtn.textContent = '×';
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (s.id !== activeSlotId) {
          switchSlot(s.id);
        }
        deleteCurrentSlot();
      });
      card.appendChild(closeBtn);
    }

    fragment.appendChild(card);
  });

  slotList.innerHTML = '';
  slotList.appendChild(fragment);

  updateSyncIndicator();
}

function switchSlot(slotId) {
  // Save current text
  const current = getActiveSlot();
  if (current) current.text = ideaText.value;
  saveSlots(slots);

  activeSlotId = slotId;
  setActiveSlotId(slotId);

  const slot = getActiveSlot();
  ideaText.value = slot ? slot.text : '';
  renderSlotList();
  changeCounter++;
  scheduleSyncToServer();
}

function addSlot() {
  // Save current
  const current = getActiveSlot();
  if (current) current.text = ideaText.value;

  const newSlot = { id: genSlotId(), text: '', label: '' };
  slots.push(newSlot);
  saveSlots(slots);

  activeSlotId = newSlot.id;
  setActiveSlotId(activeSlotId);
  ideaText.value = '';
  renderSlotList();
  ideaText.focus();
  changeCounter++;
  scheduleSyncToServer();
}

function deleteCurrentSlot() {
  if (slots.length <= 1) return;
  const deletedId = activeSlotId;
  const idx = slots.findIndex(s => s.id === activeSlotId);
  slots.splice(idx, 1);
  activeSlotId = slots[Math.min(idx, slots.length - 1)].id;
  setActiveSlotId(activeSlotId);
  ideaText.value = getActiveSlot().text;
  saveSlots(slots);
  renderSlotList();
  // Delete from server
  fetch(`${API}/api/drafts/${deletedId}`, { method: 'DELETE' }).catch(() => {});
  changeCounter++;
  scheduleSyncToServer();
}

// --- Navigation ---
function showSection(section) {
  [inputSection, historySection].forEach(s => s.classList.add('hidden'));
  section.classList.remove('hidden');
}

$('#btn-history').addEventListener('click', () => { showSection(historySection); loadHistory(); });
$('#btn-back-from-history').addEventListener('click', () => showSection(inputSection));

// --- Auto-save current slot on input (localStorage + debounced server sync) ---
ideaText.addEventListener('input', () => {
  const slot = getActiveSlot();
  if (slot) {
    slot.text = ideaText.value;
    saveSlots(slots);
  }
  changeCounter++;
  scheduleSyncToServer();
});

// --- Add Slot ---
$('#btn-add-slot').addEventListener('click', addSlot);

// --- Server Sync (Drafts API) ---

function updateSyncIndicator() {
  const el = $('#sync-status');
  if (!el) return;
  el.classList.remove('syncing', 'sync-error');
  if (syncError === 'auth') {
    el.textContent = '認証切れ';
    el.classList.add('sync-error');
    return;
  }
  if (syncError === 'network') {
    el.textContent = '同期エラー';
    el.classList.add('sync-error');
    return;
  }
  const ts = localStorage.getItem(SYNC_STATUS_KEY);
  if (ts) {
    const d = new Date(parseInt(ts));
    el.textContent = `同期: ${d.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}`;
  }
}

function scheduleSyncToServer() {
  if (syncTimer) clearTimeout(syncTimer);
  syncTimer = setTimeout(() => syncSlotsToServer(), 2000); // 2秒のデバウンス
}

async function syncSlotsToServer() {
  if (syncInFlight) {
    scheduleSyncToServer(); // 再スケジュールして変更を失わない
    return;
  }
  syncInFlight = true;
  const counterAtStart = changeCounter; // 同期開始時のカウンター値を記録

  const el = $('#sync-status');
  if (el) { el.textContent = '同期中...'; el.classList.add('syncing'); el.classList.remove('sync-error'); }

  try {
    // Save all non-empty slots to server
    const results = await Promise.all(
      slots
        .filter(s => s.text.trim().length > 0)
        .map(s => fetch(`${API}/api/drafts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: s.id, content: s.text }),
        }).catch(() => ({ status: 0, ok: false })))
    );

    // 401チェック — 1つでも認証エラーなら認証画面へ
    if (results.some(r => r.status === 401)) {
      syncError = 'auth';
      console.warn('Sync failed: session expired');
      checkAuth();
      return;
    }
    if (results.some(r => !r.ok)) {
      syncError = 'network';
      return;
    }

    // Also save slot metadata (order, active slot)
    const metaRes = await fetch(`${API}/api/drafts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: '__slot_meta__',
        content: JSON.stringify({
          slot_ids: slots.map(s => s.id),
          active_slot_id: activeSlotId,
        }),
      }),
    }).catch(() => ({ status: 0, ok: false }));

    if (metaRes.status === 401) {
      syncError = 'auth';
      checkAuth();
      return;
    }
    if (!metaRes.ok) {
      syncError = 'network';
      return;
    }

    syncError = null;
    syncedCounter = counterAtStart; // 同期開始以降に新たな変更がなければ最新
    localStorage.setItem(SYNC_STATUS_KEY, Date.now().toString());
  } catch (e) {
    console.warn('Sync failed:', e);
    syncError = 'network';
  } finally {
    syncInFlight = false;
    updateSyncIndicator();
  }
}

async function loadSlotsFromServer() {
  try {
    const res = await fetch(`${API}/api/drafts`);
    if (res.status === 401) {
      syncError = 'auth';
      updateSyncIndicator();
      checkAuth();
      return false;
    }
    if (!res.ok) return false;
    const serverDrafts = await res.json();
    if (!serverDrafts || serverDrafts.length === 0) return false;

    // Find slot metadata
    const metaDraft = serverDrafts.find(d => d.id === '__slot_meta__');
    const contentDrafts = serverDrafts.filter(d => d.id !== '__slot_meta__');

    if (contentDrafts.length === 0) return false;

    // Build a map of server drafts
    const draftMap = {};
    for (const d of contentDrafts) {
      draftMap[d.id] = d.content;
    }

    // Determine slot order
    let slotOrder = null;
    let serverActiveSlotId = null;
    if (metaDraft) {
      try {
        const meta = JSON.parse(metaDraft.content);
        slotOrder = meta.slot_ids;
        serverActiveSlotId = meta.active_slot_id;
      } catch {}
    }

    // Merge: server drafts take priority, but keep local-only slots too
    const localSlotIds = new Set(slots.map(s => s.id));
    const serverSlotIds = new Set(Object.keys(draftMap));

    // Start with server order if available
    const mergedSlots = [];
    const processedIds = new Set();

    if (slotOrder) {
      for (const id of slotOrder) {
        if (draftMap[id] !== undefined) {
          mergedSlots.push({ id, text: draftMap[id], label: '' });
          processedIds.add(id);
        } else {
          // Slot exists in order but no content — check local
          const local = slots.find(s => s.id === id);
          if (local) {
            mergedSlots.push(local);
            processedIds.add(id);
          }
        }
      }
    }

    // Add any server drafts not in the order
    for (const id of serverSlotIds) {
      if (!processedIds.has(id)) {
        mergedSlots.push({ id, text: draftMap[id], label: '' });
        processedIds.add(id);
      }
    }

    // Add local-only non-empty slots not on server
    for (const s of slots) {
      if (!processedIds.has(s.id) && s.text.trim().length > 0) {
        mergedSlots.push(s);
        processedIds.add(s.id);
      }
    }

    if (mergedSlots.length === 0) return false;

    slots = mergedSlots;
    saveSlots(slots);

    // Restore active slot
    if (serverActiveSlotId && slots.find(s => s.id === serverActiveSlotId)) {
      activeSlotId = serverActiveSlotId;
    } else {
      activeSlotId = slots[0].id;
    }
    setActiveSlotId(activeSlotId);

    return true;
  } catch (e) {
    console.warn('Failed to load server drafts:', e);
    return false;
  }
}

// --- Submit ---
$('#btn-submit').addEventListener('click', async () => {
  const text = ideaText.value.trim();
  if (!text) return;

  const btn = $('#btn-submit');
  btn.disabled = true;
  submitStatus.classList.remove('hidden', 'success', 'error');

  try {
    const res = await fetch(`${API}/api/ideas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error(await res.text());
    const idea = await res.json();

    submitStatus.textContent = `投入完了 (ID: ${idea.id})`;
    submitStatus.classList.add('success');

    // Clear this slot and remove it (or clear if it's the only one)
    const slot = getActiveSlot();
    if (slot) {
      // Delete from server
      fetch(`${API}/api/drafts/${slot.id}`, { method: 'DELETE' }).catch(() => {});

      if (slots.length > 1) {
        deleteCurrentSlot();
      } else {
        slot.text = '';
        ideaText.value = '';
        saveSlots(slots);
        renderSlotList();
      }
    }

    showProgress(idea.id, 'received');
    scheduleSyncToServer();
  } catch (e) {
    submitStatus.textContent = `エラー: ${e.message}`;
    submitStatus.classList.add('error');
  } finally {
    btn.disabled = false;
  }
});

// --- Load History ---
async function loadHistory() {
  const list = $('#history-list');
  try {
    const res = await fetch(`${API}/api/ideas`);
    const ideas = await res.json();
    if (ideas.length === 0) {
      list.innerHTML = '<div class="empty">履歴はありません</div>';
      return;
    }
    list.innerHTML = ideas.map(idea => `
      <div class="list-item">
        <div class="text-preview">${escapeHtml(idea.raw_text)}</div>
        <div class="meta">
          <span>${formatDate(idea.created_at)}</span>
          <span class="status-badge status-${idea.status}">${idea.status}</span>
          ${idea.classification_json ? (() => {
            try {
              const cls = JSON.parse(idea.classification_json);
              return cls.domain ? `<span class="domain-badge">${escapeHtml(cls.domain)}</span>` : '';
            } catch { return ''; }
          })() : ''}
        </div>
        ${idea.project_path ? `<div class="meta"><span>${escapeHtml(idea.project_path)}</span></div>` : ''}
        <div class="actions">
          ${idea.status === 'failed' ? `<button class="btn btn-ghost btn-retry" data-id="${idea.id}">再試行</button>` : ''}
          <button class="btn btn-ghost btn-resubmit" data-id="${idea.id}">再投入</button>
        </div>
        ${idea.status === 'failed' ? `
          <div class="error" style="margin-top:4px;font-size:0.75rem">${escapeHtml(idea.error || '')}</div>
        ` : ''}
      </div>
    `).join('');

    list.querySelectorAll('.btn-retry').forEach(btn => {
      btn.addEventListener('click', async () => {
        btn.disabled = true;
        await fetch(`${API}/api/ideas/${btn.dataset.id}/retry`, { method: 'POST' });
        loadHistory();
      });
    });

    list.querySelectorAll('.btn-resubmit').forEach(btn => {
      btn.addEventListener('click', async () => {
        const srcIdea = ideas.find(i => i.id === btn.dataset.id);
        if (!srcIdea) return;
        btn.disabled = true;
        btn.textContent = '投入中...';
        try {
          const res = await fetch(`${API}/api/ideas`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: srcIdea.raw_text }),
          });
          if (!res.ok) throw new Error(await res.text());
          const newIdea = await res.json();
          btn.textContent = '投入済み';
          showSection(inputSection);
          showProgress(newIdea.id, 'received');
        } catch (e) {
          btn.textContent = 'エラー';
        }
      });
    });
  } catch (e) {
    list.innerHTML = `<div class="error">読み込みエラー: ${e.message}</div>`;
  }
}

// --- Progress ---
function showProgress(ideaId, status) {
  progressBar.classList.remove('hidden');
  progressBar.dataset.ideaId = ideaId;
  updateProgress(status);
}

function updateProgress(status) {
  const steps = ['received', 'classifying', 'creating', 'launching', 'active'];
  const idx = steps.indexOf(status);
  $$('.progress-step').forEach((el, i) => {
    el.classList.remove('done', 'current');
    if (i < idx) el.classList.add('done');
    else if (i === idx) el.classList.add('current');
  });
  if (status === 'active' || status === 'failed') {
    setTimeout(() => progressBar.classList.add('hidden'), 3000);
  }
}

// --- WebSocket ---
function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${proto}//${location.host}${API}/ws`);
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'idea_status' && progressBar.dataset.ideaId === msg.idea_id) {
      updateProgress(msg.status);
    }
  };
  ws.onclose = () => setTimeout(connectWS, 3000);
  ws.onerror = () => ws.close();
}

connectWS();

// --- Auth ---
async function checkAuth() {
  try {
    const res = await fetch(`${API}/api/auth/status`);
    const data = await res.json();

    // ローカル直接接続なら認証スキップ
    if (data.local_bypass) {
      authScreen.classList.add('hidden');
      mainScreen.classList.remove('hidden');
      await initSlotsFromServer();
      return;
    }

    if (data.credential_count === 0) {
      authScreen.classList.remove('hidden');
      mainScreen.classList.add('hidden');
      $('#auth-setup').classList.remove('hidden');
      $('#btn-login').classList.add('hidden');
      return;
    }

    if (!data.logged_in) {
      authScreen.classList.remove('hidden');
      mainScreen.classList.add('hidden');
      $('#auth-setup').classList.add('hidden');
      $('#btn-login').classList.remove('hidden');
      return;
    }

    // 認証済み — サーバーからドラフトを復元
    authScreen.classList.add('hidden');
    mainScreen.classList.remove('hidden');
    await initSlotsFromServer();
  } catch (e) {
    console.warn('Auth check failed:', e);
  }
}

async function initSlotsFromServer() {
  const loaded = await loadSlotsFromServer();
  if (loaded) {
    renderSlotList();
    ideaText.value = getActiveSlot()?.text || '';
  }
}

// Base64URL <-> ArrayBuffer
function b64urlToBuffer(b64url) {
  const padding = '='.repeat((4 - b64url.length % 4) % 4);
  const b64 = (b64url + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(b64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr.buffer;
}

function bufferToB64url(buf) {
  const bytes = new Uint8Array(buf);
  let str = '';
  for (const b of bytes) str += String.fromCharCode(b);
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// パスキー登録
$('#btn-register').addEventListener('click', async () => {
  const authError = $('#auth-error');
  authError.classList.add('hidden');

  try {
    const optRes = await fetch(`${API}/api/auth/register/options`, { method: 'POST' });
    const options = await optRes.json();

    options.challenge = b64urlToBuffer(options.challenge);
    options.user.id = b64urlToBuffer(options.user.id);
    if (options.excludeCredentials) {
      options.excludeCredentials = options.excludeCredentials.map(c => ({
        ...c, id: b64urlToBuffer(c.id),
      }));
    }

    const credential = await navigator.credentials.create({ publicKey: options });

    const credJSON = {
      id: bufferToB64url(credential.rawId),
      rawId: bufferToB64url(credential.rawId),
      type: credential.type,
      response: {
        attestationObject: bufferToB64url(credential.response.attestationObject),
        clientDataJSON: bufferToB64url(credential.response.clientDataJSON),
      },
    };

    const verRes = await fetch(`${API}/api/auth/register/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: credJSON }),
    });

    if (!verRes.ok) throw new Error(await verRes.text());

    authScreen.classList.add('hidden');
    mainScreen.classList.remove('hidden');
    await initSlotsFromServer();
  } catch (e) {
    authError.textContent = `登録エラー: ${e.message}`;
    authError.classList.remove('hidden');
  }
});

// パスキーログイン
$('#btn-login').addEventListener('click', async () => {
  const authError = $('#auth-error');
  authError.classList.add('hidden');

  try {
    const optRes = await fetch(`${API}/api/auth/login/options`, { method: 'POST' });
    const options = await optRes.json();

    options.challenge = b64urlToBuffer(options.challenge);
    if (options.allowCredentials) {
      options.allowCredentials = options.allowCredentials.map(c => ({
        ...c, id: b64urlToBuffer(c.id),
      }));
    }

    const assertion = await navigator.credentials.get({ publicKey: options });

    const assertJSON = {
      id: bufferToB64url(assertion.rawId),
      rawId: bufferToB64url(assertion.rawId),
      type: assertion.type,
      response: {
        authenticatorData: bufferToB64url(assertion.response.authenticatorData),
        clientDataJSON: bufferToB64url(assertion.response.clientDataJSON),
        signature: bufferToB64url(assertion.response.signature),
        userHandle: assertion.response.userHandle ? bufferToB64url(assertion.response.userHandle) : null,
      },
    };

    const verRes = await fetch(`${API}/api/auth/login/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: assertJSON }),
    });

    if (!verRes.ok) throw new Error(await verRes.text());

    authScreen.classList.add('hidden');
    mainScreen.classList.remove('hidden');
    await initSlotsFromServer();
  } catch (e) {
    authError.textContent = `ログインエラー: ${e.message}`;
    authError.classList.remove('hidden');
  }
});

// --- Visibility change: sync when returning to the app ---
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    // 未同期のローカル変更がある場合はサーバー読み込みをスキップし、
    // 先にサーバーへ送信する（上書き防止）
    if (changeCounter > syncedCounter || syncInFlight) {
      syncSlotsToServer();
      return;
    }
    // Returning to the app — load latest from server
    loadSlotsFromServer().then(loaded => {
      if (loaded) {
        renderSlotList();
        ideaText.value = getActiveSlot()?.text || '';
      }
    });
  } else {
    // Leaving the app — ensure current state is saved
    const slot = getActiveSlot();
    if (slot) slot.text = ideaText.value;
    saveSlots(slots);
    syncSlotsToServer();
  }
});

// --- beforeunload: save to server ---
window.addEventListener('beforeunload', () => {
  const slot = getActiveSlot();
  if (slot) slot.text = ideaText.value;
  saveSlots(slots);
  // Use sendBeacon for reliable save on page unload
  const slotsToSync = slots.filter(s => s.text.trim().length > 0);
  for (const s of slotsToSync) {
    navigator.sendBeacon(`${API}/api/drafts`, new Blob(
      [JSON.stringify({ id: s.id, content: s.text })],
      { type: 'application/json' }
    ));
  }
  navigator.sendBeacon(`${API}/api/drafts`, new Blob(
    [JSON.stringify({
      id: '__slot_meta__',
      content: JSON.stringify({ slot_ids: slots.map(s => s.id), active_slot_id: activeSlotId }),
    })],
    { type: 'application/json' }
  ));
});

// --- Init ---
checkAuth();
renderSlotList();
ideaText.value = getActiveSlot().text;
showSection(inputSection);

// --- Utils ---
function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso + (iso.includes('Z') || iso.includes('+') ? '' : 'Z'));
  const now = new Date();
  const diff = now - d;
  if (diff < 60000) return 'たった今';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}時間前`;
  return d.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}
