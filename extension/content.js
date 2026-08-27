// StreamSyncr Chrome Extension - Content Script
// Injected into streaming sites to extract auth tokens from localStorage

(() => {
  'use strict';

  const hostname = window.location.hostname;
  const isStreamingSite = hostname.includes('trakt.tv') || hostname.includes('anilist.co') || hostname.includes('simkl.com') || hostname.includes('wetrakr.com');
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';

  if (!isStreamingSite && !isLocalhost) return;

  console.log(`[StreamSyncr] Content script loaded on ${hostname}`);

  // ── Extract tokens from streaming sites ─────────────────────

  function extractTraktTokens() {
    const tokens = {};

    // Trakt stores id_token in localStorage
    const idToken = localStorage.getItem('id_token');
    if (idToken) tokens.id_token = idToken;

    const accessToken = localStorage.getItem('access_token');
    if (accessToken) tokens.access_token = accessToken;

    // Try to find client_id by intercepting fetch requests
    // The Trakt web app sends trakt-api-key header with every API call
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
      const [url, options] = args;
      if (options && options.headers) {
        const headers = options.headers;
        // Check for trakt-api-key header
        if (headers['trakt-api-key'] || headers.get?.('trakt-api-key')) {
          tokens.client_id = headers['trakt-api-key'] || headers.get('trakt-api-key');
          // Store it for later use
          chrome.storage.local.set({ trakt_client_id: tokens.client_id });
        }
      }
      return originalFetch.apply(this, args);
    };

    return tokens;
  }

  function extractAnilistTokens() {
    const tokens = {};

    // AniList stores access_token in localStorage
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) tokens.access_token = accessToken;

    // Also check for al_token (CSRF)
    if (window.al_token) {
      tokens.al_token = window.al_token;
    }

    return tokens;
  }

  function extractSimklTokens() {
    const tokens = {};

    // Simkl stores idToState in sessionStorage
    const idToState = sessionStorage.getItem('idToState');
    if (idToState) {
      try {
        const parsed = JSON.parse(idToState);
        tokens.idToState = parsed;
        if (parsed.access_token) tokens.access_token = parsed.access_token;
        if (parsed.client_id) tokens.client_id = parsed.client_id;
      } catch {
        tokens.idToState = idToState;
      }
    }

    // Also extract simkl session cookie from document.cookie
    const cookies = document.cookie.split(';').map(c => c.trim());
    for (const cookie of cookies) {
      if (cookie.startsWith('simkl=')) {
        tokens.session_cookie = cookie.split('=')[1];
      }
    }

    return tokens;
  }

  function extractWeTrakrUsername() {
    const tokens = {};
    // Username is in the URL: wetrakr.com/user/{username}
    const match = window.location.pathname.match(/\/user\/([^/]+)/);
    if (match) tokens.username = match[1];
    // Also check for it in the page
    const el = document.querySelector('[data-username]');
    if (el) tokens.username = el.dataset.username;
    return tokens;
  }

  // ── Auto-extract and send tokens ───────────────────────────

  async function sendTokensToBackground(service, tokens) {
    if (Object.keys(tokens).length === 0) return;

    try {
      await chrome.runtime.sendMessage({
        type: 'TOKENS_EXTRACTED',
        service,
        tokens,
      });
      console.log(`[StreamSyncr] Sent ${service} tokens to background:`, Object.keys(tokens));
    } catch (error) {
      console.error(`[StreamSyncr] Failed to send ${service} tokens:`, error);
    }
  }

  // Extract tokens on page load
  if (hostname.includes('trakt.tv')) {
    const tokens = extractTraktTokens();
    if (Object.keys(tokens).length > 0) {
      sendTokensToBackground('trakt', tokens);
    }
  } else if (hostname.includes('anilist.co')) {
    const tokens = extractAnilistTokens();
    if (Object.keys(tokens).length > 0) {
      sendTokensToBackground('anilist', tokens);
    }
  } else if (hostname.includes('simkl.com')) {
    const tokens = extractSimklTokens();
    if (Object.keys(tokens).length > 0) {
      sendTokensToBackground('simkl', tokens);
    }
  } else if (hostname.includes('wetrakr.com')) {
    const tokens = extractWeTrakrUsername();
    if (Object.keys(tokens).length > 0) {
      sendTokensToBackground('wetrakr', tokens);
    }
  }

  // ── Listen for messages from StreamSyncr app ────────────────

  if (isLocalhost) {
    window.addEventListener('message', async (event) => {
      if (event.origin !== window.location.origin) return;

      const { type, service } = event.data;

      if (type === 'REQUEST_COOKIES') {
        try {
          const response = await chrome.runtime.sendMessage({
            type: 'EXTRACT_SERVICE',
            service,
          });
          if (response.success && response.data) {
            window.postMessage({
              type: 'COOKIE_DATA',
              service,
              data: response.data,
            }, '*');
          }
        } catch (error) {
          console.error('[StreamSyncr] Failed to extract cookies:', error);
        }
      }

      if (type === 'REQUEST_ALL_COOKIES') {
        try {
          const response = await chrome.runtime.sendMessage({ type: 'EXTRACT_ALL' });
          if (response.success) {
            window.postMessage({
              type: 'ALL_COOKIE_DATA',
              data: response.data,
            }, '*');
          }
        } catch (error) {
          console.error('[StreamSyncr] Failed to extract all cookies:', error);
        }
      }

      if (type === 'SYNC_SERVICE') {
        try {
          const response = await chrome.runtime.sendMessage({
            type: 'SYNC_SERVICE',
            service,
          });
          window.postMessage({
            type: 'SYNC_RESULT',
            service,
            data: response,
          }, '*');
        } catch (error) {
          window.postMessage({
            type: 'SYNC_RESULT',
            service,
            data: { success: false, error: error.message },
          }, '*');
        }
      }

      if (type === 'SYNC_ALL') {
        try {
          const response = await chrome.runtime.sendMessage({ type: 'SYNC_ALL' });
          window.postMessage({
            type: 'ALL_SYNC_RESULT',
            data: response,
          }, '*');
        } catch (error) {
          window.postMessage({
            type: 'ALL_SYNC_RESULT',
            data: { success: false, error: error.message },
          }, '*');
        }
      }

      if (type === 'GET_EXTENSION_STATUS') {
        try {
          const response = await chrome.runtime.sendMessage({ type: 'GET_STATUS' });
          window.postMessage({
            type: 'EXTENSION_STATUS',
            data: response,
          }, '*');
        } catch (error) {
          window.postMessage({
            type: 'EXTENSION_STATUS',
            data: { success: false, error: 'Extension not available' },
          }, '*');
        }
      }

      if (type === 'SET_AUTO_SYNC') {
        try {
          await chrome.runtime.sendMessage({
            type: 'SET_AUTO_SYNC',
            enabled: event.data.enabled,
          });
        } catch (error) {
          console.error('[StreamSyncr] Failed to set auto-sync:', error);
        }
      }

      if (type === 'OPEN_SERVICE_LOGIN') {
        try {
          await chrome.runtime.sendMessage({
            type: 'OPEN_SERVICE_LOGIN',
            service,
          });
        } catch (error) {
          console.error('[StreamSyncr] Failed to open login:', error);
        }
      }
    });

    window.postMessage({
      type: 'EXTENSION_DETECTED',
      available: true,
    }, '*');
  }

  // ── Forward cookie/token updates from background ───────────

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'COOKIE_UPDATE' && isLocalhost) {
      window.postMessage({
        type: 'COOKIE_UPDATE',
        service: message.service,
        data: message.data,
      }, '*');
    }
  });
})();
