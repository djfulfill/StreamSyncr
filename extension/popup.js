// StreamSyncr Chrome Extension - Popup Script

const SERVICES = {
  imdb: { name: 'IMDb', color: '#f5c518', icon: 'IM' },
  letterboxd: { name: 'Letterboxd', color: '#00e054', icon: 'LB' },
  wetrakr: { name: 'WeTrakr', color: '#6366f1', icon: 'WT' },
  sofasidekick: { name: 'Sofa Sidekick', color: '#f97316', icon: 'SS' },
};

let autoSyncEnabled = true;

// ── Initialize ──────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  await loadStatus();
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

// ── Render Services ─────────────────────────────────────────────

function renderServices(services) {
  const container = document.getElementById('servicesList');
  container.innerHTML = '';

  for (const [serviceId, meta] of Object.entries(SERVICES)) {
    const status = services[serviceId] || { valid: false, missing: [] };
    const card = document.createElement('div');
    card.className = 'service-card';
    card.innerHTML = `
      <div class="service-icon" style="background: ${meta.color}">${meta.icon}</div>
      <div class="service-info">
        <div class="service-name">${meta.name}</div>
        <div class="service-status ${status.valid ? 'valid' : 'expired'}">
          ${status.valid ? 'Cookies valid' : status.missing.length > 0 ? `Missing: ${status.missing.join(', ')}` : 'Not connected'}
        </div>
      </div>
      <button class="service-btn ${status.valid ? 'sync' : 'login'}" data-service="${serviceId}" data-action="${status.valid ? 'sync' : 'login'}">
        ${status.valid ? 'Sync' : 'Login'}
      </button>
    `;
    container.appendChild(card);
  }
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

// ── Sync All Button ────────────────────────────────────────────

document.getElementById('syncAllBtn').addEventListener('click', async () => {
  const btn = document.getElementById('syncAllBtn');
  btn.disabled = true;
  btn.textContent = 'Syncing...';

  try {
    await chrome.runtime.sendMessage({ type: 'SYNC_ALL' });
    // Reload status after sync
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
    // Close popup after opening login
    setTimeout(() => window.close(), 500);
  }

  btn.disabled = false;
});

function setupEventListeners() {
  // Auto-sync toggle is set up above
}
