// StreamSyncr Chrome Extension - Background Service Worker
// Handles cookie extraction, auto-sync, and communication with StreamSyncr

const STREAMSYNCR_PORT = 3030;
const STREAMSYNCR_URL = `http://localhost:${STREAMSYNCR_PORT}`;

// Service definitions: which cookies each service needs
const SERVICE_COOKIES = {
  imdb: {
    domain: '.imdb.com',
    cookies: ['session-id', 'at-main', 'session-token', 'ubid-main', 'sess-at-main', 'x-main', 'aws-waf-token'],
    required: ['session-id', 'at-main', 'session-token'],
  },
  letterboxd: {
    domain: '.letterboxd.com',
    cookies: ['lfu-session', 'remember', 'com.xk72.webparts.csrf'],
    required: ['lfu-session', 'remember'],
  },
  wetrakr: {
    domain: '.wetrakr.com',
    cookies: ['wta_at', 'wta_rt'],
    required: ['wta_at', 'wta_rt'],
  },
  sofasidekick: {
    domain: '.sofasidekick.com',
    cookies: ['session-id', 'cf_clearance', '__cf_bm'],
    required: ['session-id'],
  },
};

// State
let autoSyncEnabled = true;
let syncInterval = 5 * 60 * 1000; // 5 minutes

// ── Cookie Extraction ──────────────────────────────────────────

async function extractCookiesForService(serviceId) {
  const service = SERVICE_COOKIES[serviceId];
  if (!service) return null;

  const allCookies = await chrome.cookies.getAll({ domain: service.domain });
  const extracted = {};

  for (const cookie of allCookies) {
    if (service.cookies.includes(cookie.name)) {
      extracted[cookie.name] = cookie.value;
    }
  }

  // Check if required cookies are present
  const hasAllRequired = service.required.every((name) => extracted[name]);

  return {
    service: serviceId,
    cookies: extracted,
    valid: hasAllRequired,
    timestamp: Date.now(),
    missing: service.required.filter((name) => !extracted[name]),
  };
}

async function extractAllCookies() {
  const results = {};
  for (const serviceId of Object.keys(SERVICE_COOKIES)) {
    results[serviceId] = await extractCookiesForService(serviceId);
  }
  return results;
}

// ── StreamSyncr Communication ──────────────────────────────────

async function sendCookiesToStreamSyncr(serviceId, cookieData) {
  try {
    // Try content script first (if StreamSyncr tab is open)
    const tabs = await chrome.tabs.query({ url: `http://localhost:${STREAMSYNCR_PORT}/*` });
    if (tabs.length > 0) {
      chrome.tabs.sendMessage(tabs[0].id, {
        type: 'COOKIE_UPDATE',
        service: serviceId,
        data: cookieData,
      });
      return { method: 'content_script', success: true };
    }

    // Fallback: POST directly to backend
    const response = await fetch(`${STREAMSYNCR_URL}/api/extension/cookies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ service: serviceId, ...cookieData }),
    });

    if (response.ok) {
      return { method: 'direct_post', success: true };
    }
    return { method: 'direct_post', success: false, error: await response.text() };
  } catch (error) {
    return { method: 'none', success: false, error: error.message };
  }
}

async function syncAllServices() {
  const results = {};
  for (const [serviceId, service] of Object.entries(SERVICE_COOKIES)) {
    const data = await extractCookiesForService(serviceId);
    if (data && data.valid) {
      const sendResult = await sendCookiesToStreamSyncr(serviceId, data);
      results[serviceId] = { extracted: true, synced: sendResult.success, ...sendResult };
    } else {
      results[serviceId] = { extracted: false, valid: false, missing: data?.missing || [] };
    }
  }
  return results;
}

// ── Auto-Sync via Cookie Change Listener ───────────────────────

chrome.cookies.onChanged.addListener(async (changeInfo) => {
  if (!autoSyncEnabled || changeInfo.removed) return;

  const { cookie } = changeInfo;

  // Check if this cookie belongs to a monitored service
  for (const [serviceId, service] of Object.entries(SERVICE_COOKIES)) {
    if (service.cookies.includes(cookie.name) && cookie.domain.includes(service.domain.replace('.*', ''))) {
      console.log(`[StreamSyncr] Cookie changed for ${serviceId}: ${cookie.name}`);
      const data = await extractCookiesForService(serviceId);
      if (data && data.valid) {
        await sendCookiesToStreamSyncr(serviceId, data);
      }
      break;
    }
  }
});

// ── Alarm-Based Periodic Sync ──────────────────────────────────

chrome.alarms.create('streamsyncr-sync', { periodInMinutes: 5 });

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'streamsyncr-sync' && autoSyncEnabled) {
    await syncAllServices();
  }
});

// ── Message Handler (from popup and content scripts) ───────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    switch (message.type) {
      case 'EXTRACT_ALL':
        const allData = await extractAllCookies();
        sendResponse({ success: true, data: allData });
        break;

      case 'EXTRACT_SERVICE':
        const serviceData = await extractCookiesForService(message.service);
        sendResponse({ success: true, data: serviceData });
        break;

      case 'SYNC_ALL':
        const syncResults = await syncAllServices();
        sendResponse({ success: true, data: syncResults });
        break;

      case 'SYNC_SERVICE':
        const cookieData = await extractCookiesForService(message.service);
        if (cookieData && cookieData.valid) {
          const result = await sendCookiesToStreamSyncr(message.service, cookieData);
          sendResponse({ success: true, data: result });
        } else {
          sendResponse({ success: false, error: 'Invalid or missing cookies', data: cookieData });
        }
        break;

      case 'GET_STATUS':
        const status = {
          autoSyncEnabled,
          services: {},
        };
        for (const serviceId of Object.keys(SERVICE_COOKIES)) {
          const data = await extractCookiesForService(serviceId);
          status.services[serviceId] = {
            valid: data?.valid || false,
            missing: data?.missing || [],
            lastCheck: data?.timestamp || null,
          };
        }
        sendResponse({ success: true, data: status });
        break;

      case 'SET_AUTO_SYNC':
        autoSyncEnabled = message.enabled;
        await chrome.storage.local.set({ autoSyncEnabled });
        sendResponse({ success: true });
        break;

      case 'OPEN_SERVICE_LOGIN':
        const urls = {
          imdb: 'https://www.imdb.com/registration/signin',
          letterboxd: 'https://letterboxd.com/sign-in/',
          wetrakr: 'https://wetrakr.com/login',
          sofasidekick: 'https://sofasidekick.com/login',
        };
        if (urls[message.service]) {
          chrome.tabs.create({ url: urls[message.service] });
        }
        sendResponse({ success: true });
        break;

      default:
        sendResponse({ success: false, error: 'Unknown message type' });
    }
  })();
  return true; // Keep message channel open for async response
});

// ── Initialization ─────────────────────────────────────────────

chrome.storage.local.get(['autoSyncEnabled'], (result) => {
  autoSyncEnabled = result.autoSyncEnabled !== false;
  console.log(`[StreamSyncr] Auto-sync ${autoSyncEnabled ? 'enabled' : 'disabled'}`);
});
