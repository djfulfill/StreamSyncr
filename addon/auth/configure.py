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
                    <input type="password" id="trakt_token" placeholder="For watchlist, favorites, ratings">
                    <div class="help">Get your token at <a href="https://trakt.tv/oauth/authorize" target="_blank">trakt.tv</a></div>
                </div>
                <div class="field">
                    <label>Simkl Client ID</label>
                    <input type="text" id="simkl_client_id" placeholder="Optional — for trending + tracking">
                    <div class="help">Get your client ID at <a href="https://simkl.com/settings/developer" target="_blank">simkl.com/settings/developer</a></div>
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
                    <label>IMDb Session ID</label>
                    <input type="password" id="imdb_session_id" placeholder="For IMDb ratings + watchlist">
                    <div class="help">Get from browser cookies after logging in to IMDb</div>
                </div>
                <div class="field">
                    <label>IMDb At-Main Cookie</label>
                    <input type="password" id="imdb_at_main" placeholder="Optional — for IMDb auth">
                </div>
                <div class="divider"></div>
                <div class="field">
                    <label>Letterboxd Cookies</label>
                    <input type="password" id="letterboxd_cookies" placeholder="For Letterboxd lists + ratings">
                    <div class="help">Get from browser cookies after logging in to Letterboxd</div>
                </div>
                <div class="field">
                    <label>Letterboxd CSRF Token</label>
                    <input type="password" id="letterboxd_csrf" placeholder="Optional — for Letterboxd auth">
                </div>
            </div>
        </div>

        <!-- Actions -->
        <div class="actions">
            <button class="btn btn-secondary" onclick="resetConfig()">Reset</button>
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
            'trakt_token', 'simkl_client_id', 'anilist_token',
            'wetrakr_username', 'wetrakr_access_token', 'wetrakr_refresh_token',
            'sofasidekick_session_id',
            'plex_token', 'plex_url',
            'jellyfin_api_key', 'jellyfin_url', 'jellyfin_user_id',
            'kodi_url',
            'imdb_session_id', 'imdb_at_main',
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

        function saveConfig() {
            const config = getConfig();
            localStorage.setItem(STORAGE_KEY, JSON.stringify(config));

            const configParam = encodeURIComponent(JSON.stringify(config));
            const installUrl = `${BASE_URL}/manifest.json?config=${configParam}`;

            const status = document.getElementById('status');
            status.className = 'status show success';
            status.innerHTML = `
                <strong>Configuration saved!</strong><br>
                Copy this URL and add it to Stremio:<br>
                <code style="display:block;margin-top:8px;padding:8px;background:#0f0f1a;border-radius:4px;word-break:break-all;font-size:11px">${installUrl}</code>
                <br><button onclick="copyUrl('${installUrl}')" style="margin-top:8px;padding:6px 12px;background:#e94560;color:#fff;border:none;border-radius:4px;cursor:pointer">Copy URL</button>
            `;
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
    </script>
</body>
</html>
"""
