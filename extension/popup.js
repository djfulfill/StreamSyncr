// StreamSyncr Chrome Extension - Popup Script

const SERVICES = {
  imdb: { name: 'IMDb', color: '#f5c518', icon: 'IM', category: 'tracking', auth: 'cookie' },
  letterboxd: { name: 'Letterboxd', color: '#00e054', icon: 'LB', category: 'tracking', auth: 'cookie' },
  wetrakr: { name: 'WeTrakr', color: '#6366f1', icon: 'WT', category: 'tracking', auth: 'cookie' },
  sofasidekick: { name: 'Sofa Sidekick', color: '#f97316', icon: 'SS', category: 'tracking', auth: 'cookie' },
  trakt: { name: 'Trakt', color: '#ed1c24', icon: 'TK', category: 'tracking', auth: 'cookie' },
  anilist: { name: 'AniList', color: '#02a9e0', icon: 'AL', category: 'tracking', auth: 'cookie' },
  simkl: { name: 'Simkl', color: '#ff6600', icon: 'SK', category: 'tracking', auth: 'cookie' },
  mdblist: { name: 'MDBList', color: '#e6b422', icon: 'ML', category: 'tracking', auth: 'apikey' },
  netflix: { name: 'Netflix', color: '#e50914', icon: 'NF', category: 'streaming', auth: 'cookie' },
  primevideo: { name: 'Prime Video', color: '#00a8e1', icon: 'PV', category: 'streaming', auth: 'cookie' },
  disneyplus: { name: 'Disney+', color: '#113ccf', icon: 'D+', category: 'streaming', auth: 'cookie' },
  max: { name: 'Max', color: '#6b21a8', icon: 'MX', category: 'streaming', auth: 'cookie' },
  plex: { name: 'Plex', color: '#e5a00d', icon: 'PX', category: 'mediaserver', auth: 'token' },
  jellyfin: { name: 'Jellyfin', color: '#9b59b6', icon: 'JF', category: 'mediaserver', auth: 'apikey' },
  emby: { name: 'Emby', color: '#44b381', icon: 'EB', category: 'mediaserver', auth: 'apikey' },
  tmdb: { name: 'TMDB', color: '#01d277', icon: 'TM', category: 'metadata', auth: 'apikey' },
};

let autoSyncEnabled = true;
let cloudRelayEnabled = false;

// ── Initialize ──────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  await loadStatus();
  await loadCloudRelay();
  setupEventListeners();
});

async function loadStatus() {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'GET_STATUS' });
    if (response.success) {
      autoSyncEnabled = response.data.autoSyncEnabled;
      updateAutoSyncToggle();
      renderServices(response.data.services);
      updateStatusBar(response.data.services);
    }
  } catch (error) {
    console.error('Failed to load status:', error);
  }
}

async function loadCloudRelay() {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'GET_CLOUD_RELAY' });
    if (response.success) {
      cloudRelayEnabled = response.data.enabled;
      updateCloudRelayToggle();
      updateCloudRelayStatus();
    }
  } catch (error) {
    console.error('Failed to load cloud relay:', error);
  }
}

// ── Render Services ─────────────────────────────────────────────

function renderServices(services) {
  const container = document.getElementById('servicesList');
  container.innerHTML = '';

  const categories = [
    { id: 'tracking', label: 'Tracking Services' },
    { id: 'streaming', label: 'Streaming Services' },
    { id: 'mediaserver', label: 'Media Servers' },
    { id: 'metadata', label: 'Metadata Providers' },
  ];

  for (const cat of categories) {
    const items = Object.entries(SERVICES).filter(([, m]) => m.category === cat.id);
    if (items.length === 0) continue;

    const header = document.createElement('div');
    header.className = 'section-header';
    header.textContent = cat.label;
    container.appendChild(header);

    for (const [serviceId, meta] of items) {
      container.appendChild(createServiceCard(serviceId, meta, services[serviceId]));
    }
  }
}

function createServiceCard(serviceId, meta, status) {
  const cardStatus = status || { valid: false, missing: [] };
  const card = document.createElement('div');
  card.className = 'service-card';

  const isCookieBased = meta.auth === 'cookie';

  let statusText, btnClass, btnText, btnAction;

  if (cardStatus.valid) {
    statusText = 'Connected';
    btnClass = 'sync';
    btnText = 'Sync';
    btnAction = 'sync';
  } else if (isCookieBased) {
    statusText = cardStatus.missing.length > 0 ? `Missing: ${cardStatus.missing.join(', ')}` : 'Not connected';
    btnClass = 'login';
    btnText = 'Login';
    btnAction = 'login';
  } else {
    statusText = cardStatus.missing.length > 0 ? cardStatus.missing.join(', ') : 'Not configured';
    btnClass = 'login';
    btnText = 'Configure';
    btnAction = 'configure';
  }

  card.innerHTML = `
    <div class="service-icon" style="background: ${meta.color}">${meta.icon}</div>
    <div class="service-info">
      <div class="service-name">${meta.name}</div>
      <div class="service-status ${cardStatus.valid ? 'valid' : 'expired'}">
        ${statusText}
      </div>
    </div>
    <button class="service-btn ${btnClass}" data-service="${serviceId}" data-action="${btnAction}">
      ${btnText}
    </button>
  `;
  return card;
}

function updateStatusBar(services) {
  const dot = document.getElementById('statusDot');
  const text = document.getElementById('statusText');

  const validCount = Object.values(services).filter((s) => s.valid).length;
  const totalCount = Object.keys(SERVICES).length;

  if (validCount === totalCount) {
    dot.className = 'status-dot connected';
    text.textContent = `All ${totalCount} services connected`;
  } else if (validCount > 0) {
    dot.className = 'status-dot warning';
    text.textContent = `${validCount}/${totalCount} services connected`;
  } else {
    dot.className = 'status-dot';
    text.textContent = 'No services connected';
  }
}

// ── Auto-Sync Toggle ───────────────────────────────────────────

function updateAutoSyncToggle() {
  const toggle = document.getElementById('autoSyncToggle');
  toggle.className = `toggle-switch ${autoSyncEnabled ? 'active' : ''}`;
}

document.getElementById('autoSyncToggle').addEventListener('click', async () => {
  autoSyncEnabled = !autoSyncEnabled;
  updateAutoSyncToggle();
  await chrome.runtime.sendMessage({
    type: 'SET_AUTO_SYNC',
    enabled: autoSyncEnabled,
  });
});

// ── Cloud Relay Toggle ─────────────────────────────────────────

function updateCloudRelayToggle() {
  const toggle = document.getElementById('cloudRelayToggle');
  toggle.className = `toggle-switch ${cloudRelayEnabled ? 'active' : ''}`;
}

function updateCloudRelayStatus() {
  const statusEl = document.getElementById('cloudRelayStatus');
  const configEl = document.getElementById('cloudRelayConfig');

  if (cloudRelayEnabled) {
    statusEl.textContent = 'Cloud relay active';
    statusEl.className = 'relay-status active';
    configEl.style.display = 'block';
  } else {
    statusEl.textContent = 'Cloud relay disabled';
    statusEl.className = 'relay-status';
    configEl.style.display = 'none';
  }
}

document.getElementById('cloudRelayToggle').addEventListener('click', async () => {
  cloudRelayEnabled = !cloudRelayEnabled;
  updateCloudRelayToggle();
  updateCloudRelayStatus();

  const endpoint = document.getElementById('relayEndpoint').value;
  const token = document.getElementById('relayToken').value;

  await chrome.runtime.sendMessage({
    type: 'SET_CLOUD_RELAY',
    enabled: cloudRelayEnabled,
    endpoint,
    token,
  });
});

document.getElementById('saveRelayBtn').addEventListener('click', async () => {
  const endpoint = document.getElementById('relayEndpoint').value;
  const token = document.getElementById('relayToken').value;

  await chrome.runtime.sendMessage({
    type: 'SET_CLOUD_RELAY',
    enabled: cloudRelayEnabled,
    endpoint,
    token,
  });

  const btn = document.getElementById('saveRelayBtn');
  btn.textContent = 'Saved!';
  setTimeout(() => { btn.textContent = 'Save'; }, 1500);
});

// ── Sync All Button ────────────────────────────────────────────

document.getElementById('syncAllBtn').addEventListener('click', async () => {
  const btn = document.getElementById('syncAllBtn');
  btn.disabled = true;
  btn.textContent = 'Syncing...';

  try {
    await chrome.runtime.sendMessage({ type: 'SYNC_ALL' });
    setTimeout(loadStatus, 1000);
  } catch (error) {
    console.error('Sync failed:', error);
  }

  btn.disabled = false;
  btn.textContent = 'Sync All Services';
});

// ── Service Card Actions ───────────────────────────────────────

document.getElementById('servicesList').addEventListener('click', async (e) => {
  const btn = e.target.closest('.service-btn');
  if (!btn) return;

  const serviceId = btn.dataset.service;
  const action = btn.dataset.action;

  btn.disabled = true;

  if (action === 'sync') {
    btn.textContent = 'Syncing...';
    try {
      await chrome.runtime.sendMessage({ type: 'SYNC_SERVICE', service: serviceId });
      setTimeout(loadStatus, 500);
    } catch (error) {
      console.error(`Failed to sync ${serviceId}:`, error);
    }
  } else if (action === 'login') {
    await chrome.runtime.sendMessage({ type: 'OPEN_SERVICE_LOGIN', service: serviceId });
    setTimeout(() => window.close(), 500);
  } else if (action === 'configure') {
    await chrome.runtime.sendMessage({ type: 'OPEN_SERVICE_CONFIG', service: serviceId });
    setTimeout(() => window.close(), 500);
  }

  btn.disabled = false;
});

function setupEventListeners() {
  // Toggles and buttons set up above
}

// ── Clear Storage Button ──────────────────────────────────────
document.getElementById('clearStorageBtn').addEventListener('click', async () => {
  const btn = document.getElementById('clearStorageBtn');
  btn.textContent = 'Clearing...';
  btn.disabled = true;

  try {
    await chrome.storage.local.clear();
    btn.textContent = '✓ Cleared!';
    btn.style.background = '#22c55e';
    btn.style.color = '#fff';
    btn.style.borderColor = '#22c55e';
    setTimeout(() => {
      btn.textContent = 'Clear Extension Storage';
      btn.style.background = '#1e1e2e';
      btn.style.color = '#6b7280';
      btn.style.borderColor = '#374151';
      btn.disabled = false;
      loadStatus();
    }, 1500);
  } catch (error) {
    btn.textContent = 'Failed';
    btn.style.background = '#ef4444';
    btn.style.color = '#fff';
    setTimeout(() => {
      btn.textContent = 'Clear Extension Storage';
      btn.style.background = '#1e1e2e';
      btn.style.color = '#6b7280';
      btn.style.borderColor = '#374151';
      btn.disabled = false;
    }, 1500);
  }
});
