CONFIGURE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamSyncr — Configure</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f1a; color: #e0e0e0; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 32px 24px; text-align: center; border-bottom: 1px solid #2a2a4a; }
        .header h1 { font-size: 28px; margin-bottom: 8px; background: linear-gradient(90deg, #e94560, #ff6b6b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { color: #888; font-size: 14px; }
        .container { max-width: 640px; margin: 0 auto; padding: 24px; }
        .section { background: #16213e; border-radius: 12px; margin-bottom: 20px; overflow: hidden; }
        .section-header { padding: 16px 20px; border-bottom: 1px solid #2a2a4a; display: flex; align-items: center; gap: 12px; cursor: pointer; }
        .section-header:hover { background: #1a2a4a; }
        .section-header .icon { font-size: 20px; }
        .section-header h2 { font-size: 16px; font-weight: 600; }
        .section-header .badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: #e94560; color: #fff; margin-left: auto; }
        .section-header .badge.required { background: #e94560; }
        .section-header .badge.optional { background: #2ecc71; }
        .section-header .chevron { margin-left: auto; transition: transform 0.2s; }
        .section-header.open .chevron { transform: rotate(180deg); }
        .section-body { padding: 20px; display: none; }
        .section-body.open { display: block; }
        .field { margin-bottom: 16px; }
        .field:last-child { margin-bottom: 0; }
        .field label { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #ccc; }
        .field input, .field select { width: 100%; padding: 10px 12px; border: 1px solid #2a2a4a; border-radius: 8px; background: #0f0f1a; color: #fff; font-size: 14px; transition: border-color 0.2s; }
        .field input:focus, .field select:focus { outline: none; border-color: #e94560; }
        .field input::placeholder { color: #4a4a6a; }
        .field .help { font-size: 12px; color: #6a6a8a; margin-top: 4px; }
        .field .help a { color: #e94560; text-decoration: none; }
        .field .help a:hover { text-decoration: underline; }
        .field-row { display: flex; gap: 12px; }
        .field-row .field { flex: 1; }
        .actions { padding: 20px; display: flex; gap: 12px; }
        .btn { flex: 1; padding: 12px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-primary { background: linear-gradient(135deg, #e94560, #ff6b6b); color: #fff; }
        .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(233, 69, 96, 0.3); }
        .btn-secondary { background: #2a2a4a; color: #ccc; }
        .btn-secondary:hover { background: #3a3a5a; }
        .status { padding: 12px 20px; background: #1a2a3e; border-top: 1px solid #2a2a4a; display: none; }
        .status.show { display: block; }
        .status.success { color: #2ecc71; }
        .status.error { color: #e74c3c; }
        .footer { text-align: center; padding: 24px; color: #4a4a6a; font-size: 12px; }
        .divider { height: 1px; background: #2a2a4a; margin: 16px 0; }
        .service-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .service-card { background: #0f0f1a; border: 1px solid #2a2a4a; border-radius: 8px; padding: 12px; }
        .service-card h3 { font-size: 14px; margin-bottom: 4px; }
        .service-card p { font-size: 11px; color: #6a6a8a; }
        .btn-connect { padding: 10px 16px; background: #2a2a4a; color: #ccc; border: 1px solid #3a3a5a; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; white-space: nowrap; transition: all 0.2s; }
        .btn-connect:hover { background: #e94560; color: #fff; border-color: #e94560; }
        .btn-connect.connected { background: #2ecc71; color: #fff; border-color: #2ecc71; }
    </style>
</head>
<body>
    <div class="header">
        <h1>StreamSyncr</h1>
        <p>Configure your streaming addon — all keys are stored locally in your browser</p>
    </div>

    <div class="container">
        <!-- Debrid Services -->
        <div class="section">
            <div class="section-header open" onclick="toggleSection(this)">
                <span class="icon">🔗</span>
                <h2>Debrid Services</h2>
                <span class="badge required">Required for Streams</span>
                <span class="chevron">▼</span>
            </div>
            <div class="section-body open">
                <div class="field">
                    <label>Real-Debrid API Key</label>
                    <input type="password" id="realdebrid_key" placeholder="Optional — enables RD streams">
                    <div class="help">Get your API key at <a href="https://real-debrid.com/apitoken" target="_blank">real-debrid.com/apitoken</a></div>
                </div>
                <div class="field">
                    <label>TorBox API Key</label>
                    <input type="password" id="torbox_key" placeholder="Optional — enables TorBox streams">
                    <div class="help">Get your API key at <a href="https://torbox.app/settings" target="_blank">torbox.app/settings</a></div>
                </div>
                <div class="field">
                    <label>AllDebrid API Key</label>
                    <input type="password" id="alldebrid_key" placeholder="Optional — enables AD streams">
                    <div class="help">Get your API key at <a href="https://alldebrid.com/api" target="_blank">alldebrid.com/api</a></div>
                </div>
            </div>
        </div>

        <!-- Tracking Services -->
        <div class="section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="icon">📊</span>
                <h2>Tracking & Lists</h2>
                <span class="badge optional">Optional</span>
                <span class="chevron">▼</span>
            </div>
            <div class="section-body">
                <div class="field">
                    <label>Trakt Token</label>
                    <div style="display:flex;gap:8px;">
                        <input type="password" id="trakt_token" placeholder="Auto-filled by OAuth, or paste manually" style="flex:1;">
                        <button onclick="connectOAuth('trakt')" id="btn-trakt" class="btn-connect">Connect</button>
                    </div>
                    <div class="help">One-clicked redirects to <a href="https://app.trakt.tv" target="_blank">app.trakt.tv</a> to authorize, then auto-fills your token</div>
                </div>
                <div class="field">
                    <label>Trakt Client ID <span style="color:#e94560;font-weight:bold">★ Required for trending catalogs</span></label>
                    <input type="text" id="trakt_client_id" placeholder="Your Trakt API client_id" style="border-color:#e94560;">
                    <div class="help">
                        <strong>How to get it:</strong><br>
                        1. Go to <a href="https://app.trakt.tv/settings/apps/api" target="_blank">app.trakt.tv/settings/apps/api</a><br>
                        2. Click "New Application"<br>
                        3. Enter any name (e.g. "StreamSyncr")<br>
                        4. Copy the <code>Client ID</code> (not the secret)
                    </div>
                </div>
                <div class="field">
                    <label>Simkl Client ID <span style="color:#e94560;font-weight:bold">★ Required for trending catalogs</span></label>
                    <input type="text" id="simkl_client_id" placeholder="Your Simkl API client_id" style="border-color:#e94560;">
                    <div class="help">
                        <strong>How to get it:</strong><br>
                        1. Go to <a href="https://simkl.com/settings/developer" target="_blank">simkl.com/settings/developer</a><br>
                        2. Click "Create New App"<br>
                        3. Enter any name (e.g. "StreamSyncr")<br>
                        4. Copy the <code>Client ID</code>
                    </div>
                </div>
                <div class="field">
                    <label>AniList Token (optional)</label>
                    <input type="password" id="anilist_token" placeholder="For anime tracking">
                    <div class="help">Public anime catalogs work without a token</div>
                </div>
            </div>
        </div>

        <!-- WeTrakr -->
        <div class="section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="icon">⭐</span>
                <h2>WeTrakr</h2>
                <span class="badge optional">Optional</span>
                <span class="chevron">▼</span>
            </div>
            <div class="section-body">
                <div class="field">
                    <label>Username</label>
                    <input type="text" id="wetrakr_username" placeholder="Your WeTrakr username">
                </div>
                <div class="field">
                    <label>Access Token (wta_at)</label>
                    <input type="password" id="wetrakr_access_token" placeholder="Access token from WeTrakr">
                    <div class="help">Find in browser cookies: <code>wta_at</code></div>
                </div>
                <div class="field">
                    <label>Refresh Token (wta_rt)</label>
                    <input type="password" id="wetrakr_refresh_token" placeholder="Refresh token from WeTrakr">
                    <div class="help">Find in browser cookies: <code>wta_rt</code></div>
                </div>
            </div>
        </div>

        <!-- Sofa Sidekick -->
        <div class="section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="icon">🛋️</span>
                <h2>Sofa Sidekick</h2>
                <span class="badge optional">Optional</span>
                <span class="chevron">▼</span>
            </div>
            <div class="section-body">
                <div class="field">
                    <label>Session ID</label>
                    <input type="password" id="sofasidekick_session_id" placeholder="Your Sofa Sidekick session">
                    <div class="help">Find in browser cookies after logging in to <a href="https://app.sofasidekick.com" target="_blank">sofasidekick.com</a></div>
                </div>
                <div class="field">
                    <label>CF Clearance <span style="color:#666;font-weight:normal">(optional)</span></label>
                    <input type="password" id="sofasidekick_cf_clearance" placeholder="cf_clearance cookie">
                </div>
                <div class="field">
                    <label>CF Bot Manager <span style="color:#666;font-weight:normal">(optional)</span></label>
                    <input type="password" id="sofasidekick_cf_bm" placeholder="__cf_bm cookie">
                </div>
            </div>
        </div>

        <!-- Media Servers -->
        <div class="section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="icon">🖥️</span>
                <h2>Media Servers</h2>
                <span class="badge optional">Optional</span>
                <span class="chevron">▼</span>
            </div>
            <div class="section-body">
                <div class="field">
                    <label>Plex Token</label>
                    <input type="password" id="plex_token" placeholder="For Plex library catalogs">
                    <div class="help">Get your token at <a href="https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/" target="_blank">Plex support</a></div>
                </div>
                <div class="field">
                    <label>Plex Server URL</label>
                    <input type="text" id="plex_url" placeholder="http://192.168.1.100:32400">
                </div>
                <div class="divider"></div>
                <div class="field">
                    <label>Jellyfin API Key</label>
                    <input type="password" id="jellyfin_api_key" placeholder="For Jellyfin library catalogs">
                    <div class="help">Get your API key in Jellyfin Dashboard → API Keys</div>
                </div>
                <div class="field">
                    <label>Jellyfin Server URL</label>
                    <input type="text" id="jellyfin_url" placeholder="http://192.168.1.100:8096">
                </div>
                <div class="field">
                    <label>Jellyfin User ID</label>
                    <input type="text" id="jellyfin_user_id" placeholder="Optional — for user-specific data">
                </div>
                <div class="divider"></div>
                <div class="field">
                    <label>Kodi JSON-RPC URL</label>
                    <input type="text" id="kodi_url" placeholder="http://192.168.1.100:8080">
                    <div class="help">Enable remote control in Kodi → Settings → Services → Control</div>
                </div>
            </div>
        </div>

        <!-- Metadata Sources -->
        <div class="section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="icon">🎬</span>
                <h2>Metadata & Ratings</h2>
                <span class="badge optional">Optional</span>
                <span class="chevron">▼</span>
            </div>
            <div class="section-body">
                <div class="field">
                    <label>TMDB API Key</label>
                    <input type="password" id="tmdb_api_key" placeholder="Required for metadata, posters, ratings">
                    <div class="help">Get free API key at <a href="https://www.themoviedb.org/settings/api" target="_blank">themoviedb.org/settings/api</a></div>
                </div>
                <div class="divider"></div>
                <div class="field">
                    <label>IMDb API Key <span style="color:#666;font-weight:normal">(optional)</span></label>
                    <input type="password" id="imdb_api_key" placeholder="Optional — for metadata">
                    <div class="help">Get from <a href="https://developer.imdb.com" target="_blank">developer.imdb.com</a></div>
                </div>
                <div style="background:#1a2a3e;border:1px solid #e94560;border-radius:8px;padding:16px;margin:12px 0;">
                    <div style="color:#e94560;font-weight:bold;margin-bottom:8px;">IMDb Cookies (Required for lists, ratings, watchlist)</div>
                    <div class="help" style="margin-bottom:12px;color:#aaa;">
                        <strong>How to get it:</strong><br>
                        1. Go to <a href="https://www.imdb.com" target="_blank">imdb.com</a> and log in<br>
                        2. Press F12 → Network tab → click any request → Headers → Cookie<br>
                        3. Copy the entire cookie string and paste below
                    </div>
                </div>
                <div class="field">
                    <label>Full Cookie String</label>
                    <input type="password" id="imdb_full_cookies" placeholder="session-id=...; at-main=...; session-token=...">
                    <div class="help">Paste entire Cookie header from DevTools → Network → Headers</div>
                </div>
                <div class="divider"></div>
                <div class="field">
                    <label>Letterboxd Cookies</label>
                    <input type="password" id="letterboxd_cookies" placeholder="cf_clearance + letterboxd.user.CURRENT + com.xk72.webparts.csrf">
                    <div class="help">Browser cookies from <a href="https://letterboxd.com" target="_blank">letterboxd.com</a> — need all three</div>
                </div>
                <div class="field">
                    <label>Letterboxd CSRF Token</label>
                    <input type="password" id="letterboxd_csrf" placeholder="Value of com.xk72.webparts.csrf cookie">
                </div>
            </div>
        </div>

        <!-- MDBList -->
        <div class="section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="icon">📋</span>
                <h2>MDBList</h2>
                <span class="badge optional">Optional</span>
                <span class="chevron">▼</span>
            </div>
            <div class="section-body">
                <div class="field">
                    <label>MDBList API Key</label>
                    <input type="password" id="mdblist_api_key" placeholder="For multi-rating lists + search">
                    <div class="help">Get your free API key at <a href="https://mdblist.com/preferences/#api" target="_blank">mdblist.com/preferences/#api</a></div>
                </div>
            </div>
        </div>

        <!-- Actions -->
        <div class="actions">
            <button class="btn btn-secondary" onclick="resetConfig()">Reset</button>
            <button class="btn btn-secondary" onclick="exportData()" style="background:#2ecc71;color:#fff">Export Data</button>
            <button class="btn btn-primary" onclick="saveConfig()">Save & Install</button>
        </div>

        <div class="status" id="status"></div>
    </div>

    <div class="footer">
        StreamSyncr Addon v1.0.0 • All keys stored in your browser only
    </div>

    <script>
        const STORAGE_KEY = 'streamsyncr_config';
        const BASE_URL = window.location.origin;

        const FIELDS = [
            'realdebrid_key', 'torbox_key', 'alldebrid_key',
            'trakt_token', 'trakt_client_id', 'simkl_client_id', 'anilist_token',
            'tmdb_api_key', 'imdb_api_key',
            'mdblist_api_key',
            'wetrakr_username', 'wetrakr_access_token', 'wetrakr_refresh_token',
            'sofasidekick_session_id', 'sofasidekick_cf_clearance', 'sofasidekick_cf_bm',
            'plex_token', 'plex_url',
            'jellyfin_api_key', 'jellyfin_url', 'jellyfin_user_id',
            'kodi_url',
            'imdb_full_cookies',
            'letterboxd_cookies', 'letterboxd_csrf'
        ];

        // Load saved config
        document.addEventListener('DOMContentLoaded', () => {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                try {
                    const config = JSON.parse(saved);
                    FIELDS.forEach(key => {
                        const el = document.getElementById(key);
                        if (el && config[key]) el.value = config[key];
                    });
                } catch(e) {}
            }
        });

        function toggleSection(header) {
            header.classList.toggle('open');
            const body = header.nextElementSibling;
            body.classList.toggle('open');
        }

        function getConfig() {
            const config = {};
            FIELDS.forEach(key => {
                const val = document.getElementById(key).value.trim();
                if (val) config[key] = val;
            });
            return config;
        }

        // ── OAuth: One-Click Connect ─────────────────────

        let oauthPopup = null;

        async function connectOAuth(service) {
            const btn = document.getElementById('btn-' + service);
            btn.textContent = 'Connecting...';
            btn.disabled = true;

            // Open the OAuth authorize endpoint in a popup
            const url = `${BASE_URL}/api/oauth/${service}/authorize`;
            const w = 600, h = 700;
            const left = (screen.width - w) / 2;
            const top = (screen.height - h) / 2;
            oauthPopup = window.open(url, 'oauth_' + service,
                `width=${w},height=${h},left=${left},top=${top}`);

            // Reset button after timeout (popup blocked or cancelled)
            setTimeout(() => {
                if (oauthPopup && !oauthPopup.closed) return;
                btn.textContent = 'Connect';
                btn.disabled = false;
            }, 6000);
        }

        // Listen for OAuth token from callback popup
        window.addEventListener('message', function(e) {
            if (!e.data || !e.data.service) return;
            const {service, field_id, token, error} = e.data;
            const btn = document.getElementById('btn-' + service);

            if (token) {
                const field = document.getElementById(field_id);
                if (field) field.value = token;
                if (btn) {
                    btn.textContent = '✓ Connected';
                    btn.classList.add('connected');
                    btn.disabled = false;
                }
                const status = document.getElementById('status');
                status.className = 'status show success';
                status.textContent = `${service.charAt(0).toUpperCase() + service.slice(1)} connected! Token auto-filled.`;
            } else {
                if (btn) {
                    btn.textContent = 'Connect';
                    btn.disabled = false;
                }
                const status = document.getElementById('status');
                status.className = 'status show';
                status.style.color = '#e74c3c';
                status.textContent = `Failed: ${error || 'unknown'}`;
            }
        });

        function encodeConfigToken(config) {
            const json = JSON.stringify(config, Object.keys(config).sort());
            return btoa(json).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
        }

        async function saveConfig() {
            const config = getConfig();
            localStorage.setItem(STORAGE_KEY, JSON.stringify(config));

            const status = document.getElementById('status');
            status.className = 'status show';
            status.style.color = '#f39c12';
            status.textContent = 'Saving configuration securely...';

            try {
                // POST config to server, get back an opaque token — API keys NEVER appear in the URL
                const resp = await fetch(`${BASE_URL}/api/save-config`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ config })
                });
                const data = await resp.json();
                const token = data.token;

                const installUrl = `${BASE_URL}/${token}/manifest.json`;

                status.className = 'status show success';
                status.innerHTML = `
                    <strong>Configuration saved!</strong><br>
                    Copy this URL and add it to Stremio:<br>
                    <code style="display:block;margin-top:8px;padding:8px;background:#0f0f1a;border-radius:4px;word-break:break-all;font-size:11px">${installUrl}</code>
                    <br><button onclick="copyUrl('${installUrl}')" style="margin-top:8px;padding:6px 12px;background:#e94560;color:#fff;border:none;border-radius:4px;cursor:pointer">Copy URL</button>
                `;
            } catch (err) {
                status.className = 'status show';
                status.style.color = '#e74c3c';
                status.textContent = 'Failed to save: ' + err.message;
            }
        }

        function copyUrl(url) {
            navigator.clipboard.writeText(url).then(() => {
                const status = document.getElementById('status');
                status.innerHTML += '<br><span style="color:#2ecc71">✓ Copied to clipboard!</span>';
            });
        }

        function resetConfig() {
            localStorage.removeItem(STORAGE_KEY);
            FIELDS.forEach(key => {
                const el = document.getElementById(key);
                if (el) el.value = '';
            });
            const status = document.getElementById('status');
            status.className = 'status show';
            status.style.color = '#f39c12';
            status.textContent = 'Configuration reset.';
        }

        async function exportData() {
            const status = document.getElementById('status');
            const saved = localStorage.getItem(STORAGE_KEY);
            if (!saved) {
                status.className = 'status show';
                status.style.color = '#e74c3c';
                status.textContent = 'Save your config first before exporting.';
                return;
            }

            // First save to get a token
            status.className = 'status show';
            status.style.color = '#f39c12';
            status.textContent = 'Exporting data from all connected services...';

            try {
                const config = JSON.parse(saved);
                const saveResp = await fetch(`${BASE_URL}/api/save-config`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ config })
                });
                const { token } = await saveResp.json();

                const exportResp = await fetch(`${BASE_URL}/api/export/${token}`);
                const data = await exportResp.json();

                // Download as JSON
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `streamsyncr-export-${new Date().toISOString().slice(0,10)}.json`;
                a.click();
                URL.revokeObjectURL(url);

                status.className = 'status show success';
                const serviceCount = Object.keys(data.services).length;
                status.textContent = `Exported data from ${serviceCount} service${serviceCount !== 1 ? 's' : ''}. Download started.`;
            } catch (err) {
                status.className = 'status show';
                status.style.color = '#e74c3c';
                status.textContent = 'Export failed: ' + err.message;
            }
        }
    </script>
</body>
</html>
"""
