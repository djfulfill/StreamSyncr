// StreamSyncr Chrome Extension - Content Script
// Injected into StreamSyncr's web UI to bridge cookie data via postMessage

(() => {
  'use strict';

  // Only run on StreamSyncr pages
  if (!window.location.hostname === 'localhost' && !window.location.hostname === '127.0.0.1') {
    return;
  }

  console.log('[StreamSyncr] Content script loaded');

  // ── Listen for messages from the StreamSyncr React app ─────
  window.addEventListener('message', async (event) => {
    // Only accept messages from the same origin
    if (event.origin !== window.location.origin) return;

    const { type, service } = event.data;

    if (type === 'REQUEST_COOKIES') {
      // React app is requesting cookies for a service
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
        window.postMessage({
          type: 'COOKIE_ERROR',
          service,
          error: error.message,
        }, '*');
      }
    }

    if (type === 'REQUEST_ALL_COOKIES') {
      // React app is requesting all cookies
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
      // React app wants to sync a specific service
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
      // React app wants to sync all services
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
      // React app wants to know if extension is installed and status
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

  // ── Notify React app that extension is available ───────────
  window.postMessage({
    type: 'EXTENSION_DETECTED',
    available: true,
  }, '*');

  // ── Forward cookie changes from background to React app ────
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'COOKIE_UPDATE') {
      window.postMessage({
        type: 'COOKIE_UPDATE',
        service: message.service,
        data: message.data,
      }, '*');
    }
  });
})();
