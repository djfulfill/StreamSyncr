CONFIGURE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamSyncr — Configure</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root { --blue: #3b82f6; --blue-glow: #60a5fa; --purple: #a855f7; --magenta: #e879f9; --dark: #030712; --dark-card: #0a0f1e; --dark-border: #1e293b; --text: #f8fafc; --text-muted: #94a3b8; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', sans-serif; background: var(--dark); color: var(--text); min-height: 100vh; line-height: 1.6; }
.header { background: linear-gradient(135deg, rgba(10, 15, 30, 0.95), rgba(3, 7, 18, 0.97)); padding: 32px 24px; text-align: center; border-bottom: 1px solid rgba(59, 130, 246, 0.15); position: relative; }
.header::before { content: ''; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 800px; height: 800px; background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%); pointer-events: none; }
.header h1 { font-family: 'Orbitron', sans-serif; font-size: 28px; font-weight: 800; margin-bottom: 8px; background: linear-gradient(135deg, var(--blue), var(--purple), var(--magenta)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header p { color: var(--text-muted); font-size: 14px; }
.container { max-width: 640px; margin: 0 auto; padding: 24px; position: relative; z-index: 1; }
.section { background: linear-gradient(135deg, rgba(10, 15, 30, 0.85), rgba(5, 10, 25, 0.95)); backdrop-filter: blur(20px); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 16px; margin-bottom: 20px; overflow: hidden; position: relative; }
.section:hover { border-color: rgba(59, 130, 246, 0.35); box-shadow: 0 0 30px rgba(59, 130, 246, 0.1); }
.section-header { padding: 16px 20px; border-bottom: 1px solid rgba(59, 130, 246, 0.15); display: flex; align-items: center; gap: 12px; cursor: pointer; transition: background 0.3s; }
.section-header:hover { background: rgba(59, 130, 246, 0.08); }
.section-header .icon { font-size: 20px; }
.section-header h2 { font-family: 'Orbitron', sans-serif; font-size: 16px; font-weight: 600; color: var(--text); }
.section-header .badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: linear-gradient(135deg, var(--blue), var(--purple)); color: #fff; margin-left: auto; font-weight: 500; }
.section-header .badge.required { background: linear-gradient(135deg, var(--blue), var(--blue-glow)); }
.section-header .badge.optional { background: linear-gradient(135deg, var(--purple), var(--magenta)); }
.section-header .chevron { margin-left: 12px; transition: transform 0.2s; color: var(--text-muted); }
.section-header.open .chevron { transform: rotate(180deg); }
.section-body { padding: 20px; display: none; }
.section-body.open { display: block; }
.field { margin-bottom: 16px; }
.field:last-child { margin-bottom: 0; }
.field label { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: var(--text-muted); }
.field input, .field select { width: 100%; padding: 10px 12px; border: 1px solid var(--dark-border); border-radius: 8px; background: rgba(3, 7, 18, 0.7); color: var(--text); font-size: 14px; transition: border-color 0.2s; font-family: 'Inter', sans-serif; }
.field input:focus, .field select:focus { outline: none; border-color: var(--blue); box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
.field input::placeholder { color: rgba(148, 163, 184, 0.5); }
.field .help { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.field .help a { color: var(--blue-glow); text-decoration: none; transition: color 0.2s; }
.field .help a:hover { color: var(--magenta); text-decoration: underline; }
.field-row { display: flex; gap: 12px; }
.field-row .field { flex: 1; }
.actions { padding: 20px; display: flex; gap: 12px; }
.btn { flex: 1; padding: 12px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-family: 'Orbitron', sans-serif; }
.btn-primary { background: linear-gradient(135deg, var(--blue), var(--purple)); color: #fff; box-shadow: 0 0 20px rgba(59, 130, 246, 0.3); }
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 0 30px rgba(59, 130, 246, 0.5); }
.btn-secondary { background: rgba(255, 255, 255, 0.06); color: var(--text-muted); border: 1px solid var(--dark-border); }
.btn-secondary:hover { background: rgba(59, 130, 246, 0.15); color: var(--text); border-color: var(--blue); }
.status { padding: 12px 20px; background: rgba(10, 15, 30, 0.9); border-top: 1px solid rgba(59, 130, 246, 0.2); display: none; }
.status.show { display: block; }
.status.success { color: #55efc4; }
.status.error { color: #fd79a8; }
.footer { text-align: center; padding: 24px; color: var(--text-muted); font-size: 12px; font-family: 'Inter', sans-serif; }
.divider { height: 1px; background: var(--dark-border); margin: 16px 0; }
.service-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.service-card { background: rgba(3, 7, 18, 0.6); border: 1px solid var(--dark-border); border-radius: 8px; padding: 12px; }
.service-card h3 { font-size: 14px; margin-bottom: 4px; color: var(--text); }
.service-card p { font-size: 11px; color: var(--text-muted); }
.btn-connect { padding: 10px 16px; background: rgba(255, 255, 255, 0.06); color: var(--text-muted); border: 1px solid var(--dark-border); border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; white-space: nowrap; transition: all 0.2s; font-family: 'Inter', sans-serif; }
.btn-connect:hover { background: linear-gradient(135deg, var(--blue), var(--purple)); color: #fff; border-color: transparent; box-shadow: 0 0 15px rgba(59, 130, 246, 0.3); }
.btn-connect.connected { background: linear-gradient(135deg, #55efc4, #00b859); color: #fff; border-color: transparent; box-shadow: 0 0 15px rgba(85, 239, 196, 0.3); }
</style>

</head>
<body>
    <div class="header">
        <h1>StreamSyncr</h1>
        <p>Configure your streaming addon — all keys are stored locally in your browser</p>
    </div>

    <!-- Service Status Dashboard -->
    <div class="container" id="status-dashboard" style="display:none; padding-bottom: 0;">
        <div class="section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="icon">📡</span>
                <h2>Service Status</h2>
                <span class="badge" id="status-summary">—</span>
                <span class="chevron">▼</span>
            </div>
            <div class="section-body open">
                <div id="service-status-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:8px;"></div>
                <div style="margin-top:12px;text-align:center;">
                    <button onclick="verifyAllServices()" class="btn-connect" id="btn-verify" style="width:100%;">Verify Connections</button>
                </div>
            </div>
        </div>
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

        <!-- Sootio Stream Backend -->
        <div class="section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="icon">🚀</span>
                <h2>Sootio Stream Backend</h2>
                <span class="badge optional">Optional — Enhanced Streams</span>
                <span class="chevron">▼</span>
            </div>
            <div class="section-body">
                <div class="field">
                    <label>Sootio URL</label>
                    <input type="text" id="sootio_url" placeholder="http://localhost:7000">
                    <div class="help">URL of your local Sootio addon server. Leave blank to use default (http://localhost:7000).</div>
                </div>
                <div class="field">
                    <label>Enable Sootio Backend</label>
                    <select id="sootio_enabled">
                        <option value="true">Enabled (use Sootio for stream resolution, fall back to built-in)</option>
                        <option value="false">Disabled (use built-in Torrentio/Jackett resolver only)</option>
                    </select>
                    <div class="help">Sootio provides 7 debrid providers, 14+ scrapers, and smart quality scoring. Debrid keys above are passed to Sootio automatically.</div>
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
            'sootio_url', 'sootio_enabled',
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

        // Load saved config from localStorage + server (extension-sourced)
        document.addEventListener('DOMContentLoaded', async () => {
            // 1. Load from localStorage first
            const saved = localStorage.getItem(STORAGE_KEY);
            const localConfig = saved ? JSON.parse(saved) : {};

            // 2. Fetch extension-captured config from server
            try {
                const resp = await fetch(`${BASE_URL}/api/extension/config`);
                const { config: extConfig } = await resp.json();
                // Merge: server data fills in what localStorage doesn't have
                Object.keys(extConfig).forEach(key => {
                    if (!localConfig[key] && extConfig[key]) {
                        localConfig[key] = extConfig[key];
                    }
                });
            } catch(e) {}

            // 3. Fill form fields
            FIELDS.forEach(key => {
                const el = document.getElementById(key);
                if (el && localConfig[key]) el.value = localConfig[key];
            });

            // 4. Update status grid
            updateServiceStatusGrid();
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

        // ── Service Status Dashboard ─────────────────────

        const SERVICE_LABELS = {
            realdebrid: { name: 'Real-Debrid', icon: '⚡', fields: ['realdebrid_key'] },
            torbox: { name: 'TorBox', icon: '📦', fields: ['torbox_key'] },
            alldebrid: { name: 'AllDebrid', icon: '🌐', fields: ['alldebrid_key'] },
            sootio: { name: 'Sootio', icon: '🚀', fields: ['sootio_url'], optional: true },
            trakt: { name: 'Trakt', icon: '📊', fields: ['trakt_token', 'trakt_client_id'], requireAll: true },
            tmdb: { name: 'TMDB', icon: '🎬', fields: ['tmdb_api_key'] },
            simkl: { name: 'Simkl', icon: '📺', fields: ['simkl_client_id'] },
            anilist: { name: 'AniList', icon: '🎌', fields: ['anilist_token'] },
            mdblist: { name: 'MDBList', icon: '📋', fields: ['mdblist_api_key'] },
            wetrakr: { name: 'WeTrakr', icon: '⭐', fields: ['wetrakr_access_token'] },
            imdb: { name: 'IMDb', icon: '🎭', fields: ['imdb_full_cookies'] },
            letterboxd: { name: 'Letterboxd', icon: '🎬', fields: ['letterboxd_cookies', 'letterboxd_csrf'], requireAll: true },
            netflix: { name: 'Netflix', icon: '🎬', fields: ['netflix_id'] },
            primevideo: { name: 'Prime Video', icon: '🎬', fields: ['primevideo_session_id'] },
            disneyplus: { name: 'Disney+', icon: '🎬', fields: ['disneyplus_ct'] },
            max: { name: 'Max', icon: '🎬', fields: ['max_jwt'] },
            sofasidekick: { name: 'Sofa Sidekick', icon: '🛋️', fields: ['sofasidekick_session_id'] },
            plex: { name: 'Plex', icon: '🖥️', fields: ['plex_token', 'plex_url'], requireAll: true },
            jellyfin: { name: 'Jellyfin', icon: '🐋', fields: ['jellyfin_api_key', 'jellyfin_url'], requireAll: true },
            kodi: { name: 'Kodi', icon: '📡', fields: ['kodi_url'] },
        };

        function updateServiceStatusGrid() {
            const grid = document.getElementById('service-status-grid');
            const dashboard = document.getElementById('status-dashboard');
            const config = getConfig();
            const hasAnyConfig = Object.keys(config).length > 0;

            if (!hasAnyConfig) {
                dashboard.style.display = 'none';
                return;
            }

            dashboard.style.display = 'block';
            grid.innerHTML = '';

            let configuredCount = 0;
            const totalServices = Object.keys(SERVICE_LABELS).length;

            for (const [key, info] of Object.entries(SERVICE_LABELS)) {
                const isConfigured = info.requireAll
                    ? info.fields.every(f => config[f] && config[f].trim())
                    : info.fields.some(f => config[f] && config[f].trim());
                if (isConfigured) configuredCount++;

                const card = document.createElement('div');
                card.className = 'service-card';
                card.style.display = 'flex';
                card.style.alignItems = 'center';
                card.style.gap = '8px';
                card.style.padding = '8px 12px';
                card.id = 'status-' + key;

                const dot = document.createElement('span');
                dot.style.width = '8px';
                dot.style.height = '8px';
                dot.style.borderRadius = '50%';
                dot.style.flexShrink = '0';
                dot.style.transition = 'all 0.3s';

                if (isConfigured) {
                    dot.style.background = '#94a3b8';
                    dot.style.boxShadow = '0 0 6px rgba(148, 163, 184, 0.5)';
                    card.dataset.configured = 'true';
                } else {
                    dot.style.background = '#334155';
                    card.dataset.configured = 'false';
                }

                const label = document.createElement('span');
                label.style.fontSize = '12px';
                label.style.color = isConfigured ? '#f8fafc' : '#64748b';
                label.textContent = info.icon + ' ' + info.name;

                card.appendChild(dot);
                card.appendChild(label);
                grid.appendChild(card);
            }

            const summary = document.getElementById('status-summary');
            summary.textContent = configuredCount + '/' + totalServices;
            summary.style.background = configuredCount > 0
                ? 'linear-gradient(135deg, #55efc4, #00b859)'
                : 'linear-gradient(135deg, #64748b, #475569)';
        }

        async function verifyAllServices() {
            const config = getConfig();
            const btn = document.getElementById('btn-verify');
            btn.textContent = 'Verifying...';
            btn.disabled = true;

            try {
                const resp = await fetch(`${BASE_URL}/api/verify`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ config })
                });
                const results = await resp.json();

                let okCount = 0;
                let errCount = 0;

                for (const [key, result] of Object.entries(results)) {
                    const card = document.getElementById('status-' + key);
                    if (!card) continue;

                    const dot = card.querySelector('span:first-child');
                    const label = card.querySelector('span:last-child');

                    if (result.status === 'ok') {
                        dot.style.background = '#55efc4';
                        dot.style.boxShadow = '0 0 8px rgba(85, 239, 196, 0.6)';
                        label.style.color = '#55efc4';
                        okCount++;
                    } else if (result.status === 'error') {
                        dot.style.background = '#fd79a8';
                        dot.style.boxShadow = '0 0 8px rgba(253, 121, 168, 0.6)';
                        label.style.color = '#fd79a8';
                        label.title = result.error;
                        errCount++;
                    } else {
                        dot.style.background = '#334155';
                        dot.style.boxShadow = 'none';
                        label.style.color = '#64748b';
                    }
                }

                const summary = document.getElementById('status-summary');
                summary.textContent = errCount > 0 ? okCount + ' ok, ' + errCount + ' err' : okCount + ' active';
                summary.style.background = errCount > 0
                    ? 'linear-gradient(135deg, #f39c12, #e74c3c)'
                    : 'linear-gradient(135deg, #55efc4, #00b859)';
            } catch (err) {
                console.error('Verify failed:', err);
            }

            btn.textContent = 'Verify Connections';
            btn.disabled = false;
        }

        // Update dashboard on load and on any input change
        document.addEventListener('DOMContentLoaded', updateServiceStatusGrid);
        FIELDS.forEach(key => {
            const el = document.getElementById(key);
            if (el) el.addEventListener('input', updateServiceStatusGrid);
        });
    </script>
</body>
</html>
"""
