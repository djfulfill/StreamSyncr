// StreamSyncr Chrome Extension - Background Service Worker
// Handles cookie extraction, auto-sync, and communication with StreamSyncr

const STREAMSYNCR_PORT = 7800;
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
    cookies: ['session_id', 'cf_clearance', '__cf_bm'],
    required: ['session_id'],
  },
  netflix: {
    domain: '.netflix.com',
    cookies: ['NetflixId', 'SecureNetflixId', 'nfvdid', 'memclid', 'profilesNewSession'],
    required: ['NetflixId', 'SecureNetflixId'],
  },
  primevideo: {
    domain: '.primevideo.com',
    cookies: ['session-id', 'at-main', 'ubid-main', 'x-main', 'sess-at-main', 'lrc-main', 'lc-main'],
    required: ['session-id', 'at-main'],
  },
  disneyplus: {
    domain: '.disneyplus.com',
    cookies: ['ct_', 'bt_obi', 'dpong', 'amplitude_id', 'ajs_anonymous_id'],
    required: ['ct_'],
  },
  max: {
    domain: '.max.com',
    cookies: ['hb_obi', 'tp_obi', 'jwt', 'apollo-auth', 'BM-Visitor-Id'],
    required: ['jwt'],
  },
  anilist: {
    domain: '.anilist.co',
    cookies: ['laravel_session'],
    required: ['laravel_session'],
  },
  simkl: {
    domain: '.simkl.com',
    cookies: ['simkl', 'cf_clearance', '__cflb', 'cc'],
    required: ['simkl'],
  },
};

// Config-based services (API keys, not cookies)
const CONFIG_SERVICES = ['mdblist', 'plex', 'jellyfin', 'emby', 'tmdb'];

// Cloud relay endpoints (set by user via popup)
let cloudRelayEnabled = false;
let cloudRelayEndpoint = '';
let cloudRelayToken = '';

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
  const results = [];

  // Check for stored tokens (from localStorage/sessionStorage)
  const stored = await chrome.storage.local.get(`tokens_${serviceId}`);
  const tokens = stored[`tokens_${serviceId}`];

  // Merge tokens into cookie data if available
  const payload = { service: serviceId, ...cookieData };
  if (tokens) {
    payload.tokens = tokens;
    // If tokens have valid auth, mark as valid
    if (tokens.access_token || tokens.id_token || tokens.al_token) {
      payload.valid = true;
    }
  }

  // Local delivery — always POST directly to server
  try {
    const response = await fetch(`${STREAMSYNCR_URL}/api/extension/cookies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    results.push({ target: 'local', method: 'direct_post', success: response.ok, result });
  } catch (error) {
    results.push({ target: 'local', method: 'none', success: false, error: error.message });
  }

  // Cloud relay delivery (if enabled)
  if (cloudRelayEnabled && cloudRelayEndpoint) {
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (cloudRelayToken) {
        headers['Authorization'] = `Bearer ${cloudRelayToken}`;
      }
      const response = await fetch(`${cloudRelayEndpoint}/api/relay/cookies`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });
      results.push({ target: 'cloud', method: 'relay', success: response.ok });
    } catch (error) {
      results.push({ target: 'cloud', method: 'relay', success: false, error: error.message });
    }
  }

  return { results, primary: results[0] };
}

async function syncAllServices() {
  const results = {};

  // 1. Cookie-based services
  for (const [serviceId, service] of Object.entries(SERVICE_COOKIES)) {
    const data = await extractCookiesForService(serviceId);
    if (data && data.valid) {
      const sendResult = await sendCookiesToStreamSyncr(serviceId, data);
      results[serviceId] = { extracted: true, synced: sendResult.success, ...sendResult };
    } else {
      results[serviceId] = { extracted: false, valid: false, missing: data?.missing || [] };
    }
  }

  // 2. Token-based services (trakt, anilist) — send stored tokens to server
  for (const serviceId of ['trakt', 'anilist']) {
    const stored = await chrome.storage.local.get([`tokens_${serviceId}`, `${serviceId}_client_id`]);
    const tokens = stored[`tokens_${serviceId}`];
    const clientId = stored[`${serviceId}_client_id`];

    if (tokens && Object.keys(tokens).length > 0) {
      const payload = { service: serviceId, cookies: tokens, valid: true, tokens, timestamp: Date.now() };
      if (clientId) payload.cookies.client_id = clientId;

      try {
        const response = await fetch(`${STREAMSYNCR_URL}/api/extension/cookies`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const result = await response.json();
        results[serviceId] = { extracted: true, synced: response.ok, result };
      } catch (error) {
        results[serviceId] = { extracted: true, synced: false, error: error.message };
      }
    } else {
      results[serviceId] = { extracted: false, synced: false, note: 'no tokens stored' };
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
        // Cookie-based services
        for (const serviceId of Object.keys(SERVICE_COOKIES)) {
          const data = await extractCookiesForService(serviceId);
          status.services[serviceId] = {
            valid: data?.valid || false,
            missing: data?.missing || [],
            lastCheck: data?.timestamp || null,
          };
        }
        // Check for localStorage/sessionStorage tokens (trakt, anilist)
        for (const serviceId of ['trakt', 'anilist']) {
          const stored = await chrome.storage.local.get([`tokens_${serviceId}`, `${serviceId}_client_id`]);
          const tokens = stored[`tokens_${serviceId}`];
          const clientId = stored[`${serviceId}_client_id`];

          if (tokens && Object.keys(tokens).length > 0) {
            // Check for valid token based on service
            let hasValidToken = false;
            if (serviceId === 'trakt') {
              // Trakt needs both token AND client_id
              hasValidToken = !!(tokens.id_token || tokens.access_token) && !!clientId;
            } else if (serviceId === 'anilist') {
              hasValidToken = !!(tokens.access_token || tokens.al_token);
            }

            if (hasValidToken) {
              status.services[serviceId] = {
                valid: true,
                missing: [],
                lastCheck: Date.now(),
                source: 'tokens',
              };
            }
          }
          // Default if no tokens found
          if (!status.services[serviceId]) {
            const url = serviceId === 'trakt' ? 'app.trakt.tv' : serviceId + '.co';
            status.services[serviceId] = {
              valid: false,
              missing: [`visit ${url} to connect`],
              lastCheck: null,
            };
          }
        }
        // Config-based services (check with backend)
        for (const serviceId of CONFIG_SERVICES) {
          try {
            const resp = await fetch(`${STREAMSYNCR_URL}/api/extension/status/${serviceId}`);
            if (resp.ok) {
              const cfg = await resp.json();
              status.services[serviceId] = { valid: cfg.configured || false, missing: [], lastCheck: Date.now() };
            } else {
              status.services[serviceId] = { valid: false, missing: ['not configured'], lastCheck: null };
            }
          } catch {
            status.services[serviceId] = { valid: false, missing: ['server unreachable'], lastCheck: null };
          }
        }
        sendResponse({ success: true, data: status });
        break;

      case 'SET_AUTO_SYNC':
        autoSyncEnabled = message.enabled;
        await chrome.storage.local.set({ autoSyncEnabled });
        sendResponse({ success: true });
        break;

      case 'SCROBBLE_EVENT':
        // Forward scrobble events to StreamSyncr backend
        try {
          const scrobbleResponse = await fetch(`${STREAMSYNCR_URL}/api/scrobble`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Config-Token': '__extension__',
            },
            body: JSON.stringify({
              imdb_id: message.imdb_id,
              progress: message.progress,
              action: message.action,
              title: message.title,
              year: message.year,
              media_type: message.media_type || 'movie',
              client_type: 'extension',
            }),
          });
          sendResponse({ success: scrobbleResponse.ok });
        } catch (error) {
          sendResponse({ success: false, error: error.message });
        }
        break;

      case 'SET_CLOUD_RELAY':
        cloudRelayEnabled = message.enabled;
        cloudRelayEndpoint = message.endpoint || '';
        cloudRelayToken = message.token || '';
        await chrome.storage.local.set({ cloudRelayEnabled, cloudRelayEndpoint, cloudRelayToken });
        sendResponse({ success: true });
        break;

      case 'GET_CLOUD_RELAY':
        sendResponse({
          success: true,
          data: { enabled: cloudRelayEnabled, endpoint: cloudRelayEndpoint, token: cloudRelayToken },
        });
        break;

      case 'OPEN_SERVICE_LOGIN':
        const urls = {
          imdb: 'https://www.imdb.com/registration/signin',
          letterboxd: 'https://letterboxd.com/sign-in/',
          wetrakr: 'https://wetrakr.com/login',
          sofasidekick: 'https://sofasidekick.com/login',
          netflix: 'https://www.netflix.com/browse',
          primevideo: 'https://www.amazon.com/gp/video/storefront',
          disneyplus: 'https://www.disneyplus.com/login',
          max: 'https://www.max.com/sign-in',
          trakt: 'https://app.trakt.tv',
          anilist: 'https://anilist.co/login',
          simkl: 'https://simkl.com/login',
        };
        if (urls[message.service]) {
          chrome.tabs.create({ url: urls[message.service] });
        }
        sendResponse({ success: true });
        break;

      case 'OPEN_SERVICE_CONFIG':
        const configUrls = {
          trakt: 'https://app.trakt.tv',
          anilist: 'https://anilist.co/login',
          simkl: 'https://simkl.com/login',
          mdblist: 'https://mdblist.com/login',
          plex: 'https://app.plex.tv/auth#signin',
          jellyfin: 'https://jellyfin.org/docs/general/installation/',
          emby: 'https://emby.media/download.html',
          tmdb: 'https://www.themoviedb.org/settings/api',
        };
        if (configUrls[message.service]) {
          chrome.tabs.create({ url: configUrls[message.service] });
        }
        sendResponse({ success: true });
        break;

      case 'TOKENS_EXTRACTED':
        // Store tokens extracted from localStorage/sessionStorage by content script
        await chrome.storage.local.set({
          [`tokens_${message.service}`]: message.tokens,
        });
        console.log(`[StreamSyncr] Stored ${message.service} tokens:`, Object.keys(message.tokens));
        sendResponse({ success: true });
        break;

      default:
        sendResponse({ success: false, error: 'Unknown message type' });
    }
  })();
  return true; // Keep message channel open for async response
});

// ── Initialization ─────────────────────────────────────────────

chrome.storage.local.get(['autoSyncEnabled', 'cloudRelayEnabled', 'cloudRelayEndpoint', 'cloudRelayToken'], (result) => {
  autoSyncEnabled = result.autoSyncEnabled !== false;
  cloudRelayEnabled = result.cloudRelayEnabled === true;
  cloudRelayEndpoint = result.cloudRelayEndpoint || '';
  cloudRelayToken = result.cloudRelayToken || '';
  console.log(`[StreamSyncr] Auto-sync ${autoSyncEnabled ? 'enabled' : 'disabled'}, Cloud relay ${cloudRelayEnabled ? 'enabled' : 'disabled'}`);
});
