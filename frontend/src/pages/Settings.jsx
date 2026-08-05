import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Settings as SettingsIcon,
  Check,
  X,
  ExternalLink,
  Eye,
  EyeOff,
  Shield,
  Key,
  User,
  Plug,
  RefreshCw,
  Download,
  AlertTriangle,
} from 'lucide-react';
import useStore from '../store';

const services = [
  {
    id: 'wetrakr',
    name: 'StreamSyncr',
    description: 'Unofficial API. Tokens expire after ~2 days.',
    color: 'glow',
    gradient: 'from-glow to-blue-glow',
    fields: [
      { key: 'accessToken', label: 'Access Token (wta_at)', type: 'password' },
      { key: 'refreshToken', label: 'Refresh Token (wta_rt)', type: 'password' },
      { key: 'username', label: 'Username', type: 'text' },
    ],
    docsUrl: 'https://wetrakr.com',
  },
  {
    id: 'trakt',
    name: 'Trakt',
    description: 'Official API with scrobbling, lists, and social features.',
    color: 'ember',
    gradient: 'from-ember to-c084fc',
    fields: [
      { key: 'apiKey', label: 'API Key', type: 'password' },
      { key: 'token', label: 'Bearer Token', type: 'password' },
      { key: 'username', label: 'Username', type: 'text' },
    ],
    docsUrl: 'https://trakt.tv',
  },
  {
    id: 'tmdb',
    name: 'TMDB',
    description: 'Movie database with posters, metadata, and watch providers.',
    color: 'flame',
    gradient: 'from-flame to-f0abfc',
    fields: [
      { key: 'apiKey', label: 'API Key', type: 'password' },
      { key: 'username', label: 'Username', type: 'text' },
    ],
    docsUrl: 'https://themoviedb.org',
  },
  {
    id: 'imdb',
    name: 'IMDb',
    description: 'Lists, ratings, and watchlist sync via GraphQL API.',
    color: 'rose',
    gradient: 'from-rose to-fb7185',
    fields: [
      { key: 'sessionId', label: 'Session ID (session-id)', type: 'password' },
      { key: 'atMain', label: 'AT Main (at-main)', type: 'password' },
      { key: 'sessionToken', label: 'Session Token', type: 'password' },
      { key: 'ubidMain', label: 'UBID Main (optional)', type: 'password' },
      { key: 'sessAtMain', label: 'Sess AT Main (optional)', type: 'password' },
    ],
    docsUrl: 'https://www.imdb.com',
  },
  {
    id: 'plex',
    name: 'Plex',
    description: 'Official API. Use your Plex token and server URL.',
    color: 'mint',
    gradient: 'from-mint to-emerald-400',
    fields: [
      { key: 'baseUrl', label: 'Server URL (e.g. http://localhost:32400)', type: 'text' },
      { key: 'token', label: 'Plex Token', type: 'password' },
      { key: 'username', label: 'Username (optional)', type: 'text' },
    ],
    docsUrl: 'https://plex.tv',
  },
  {
    id: 'anilist',
    name: 'AniList',
    description: 'Official GraphQL API. No auth needed for reads; OAuth for writes.',
    color: 'flame',
    gradient: 'from-flame to-sky-500',
    fields: [
      { key: 'accessToken', label: 'Access Token (optional)', type: 'password' },
      { key: 'username', label: 'Username', type: 'text' },
    ],
    docsUrl: 'https://anilist.co',
  },
  {
    id: 'simkl',
    name: 'Simkl',
    description: 'Official API. Client ID required; OAuth for user data.',
    color: 'flame',
    gradient: 'from-flame to-blue-500',
    fields: [
      { key: 'clientId', label: 'Client ID', type: 'password' },
      { key: 'accessToken', label: 'Access Token (optional)', type: 'password' },
      { key: 'username', label: 'Username (optional)', type: 'text' },
    ],
    docsUrl: 'https://simkl.com',
  },
  {
    id: 'jellyfin',
    name: 'Jellyfin',
    description: 'Official API. Requires API key from admin dashboard.',
    color: 'glow',
    gradient: 'from-glow to-purple-500',
    fields: [
      { key: 'baseUrl', label: 'Server URL (e.g. http://localhost:8096)', type: 'text' },
      { key: 'apiKey', label: 'API Key', type: 'password' },
      { key: 'userId', label: 'User ID', type: 'password' },
      { key: 'username', label: 'Username (optional)', type: 'text' },
    ],
    docsUrl: 'https://jellyfin.org',
  },
  {
    id: 'kodi',
    name: 'Kodi',
    description: 'JSON-RPC API. Enable in Settings → Services → Control.',
    color: 'mint',
    gradient: 'from-mint to-blue-600',
    fields: [
      { key: 'baseUrl', label: 'Server URL (e.g. http://192.168.1.50:8080)', type: 'text' },
      { key: 'username', label: 'Username (optional)', type: 'text' },
      { key: 'password', label: 'Password (optional)', type: 'password' },
    ],
    docsUrl: 'https://kodi.tv',
  },
];

export default function Settings() {
  const store = useStore();
  const [extensionStatus, setExtensionStatus] = useState(null);
  const [extensionLoading, setExtensionLoading] = useState(true);

  // Listen for content script messages
  useEffect(() => {
    const handleMessage = (event) => {
      if (event.origin !== window.location.origin) return;

      if (event.data.type === 'EXTENSION_DETECTED') {
        store.setExtensionDetected(true);
        // Request status from extension
        window.postMessage({ type: 'GET_EXTENSION_STATUS' }, '*');
      }

      if (event.data.type === 'EXTENSION_STATUS') {
        const { data } = event.data;
        if (data.success) {
          setExtensionStatus(data.data);
          store.setExtensionConnected(true);
        }
        setExtensionLoading(false);
      }

      if (event.data.type === 'ALL_COOKIE_DATA') {
        // Auto-connect services from extension data
        const { data } = event.data;
        for (const [serviceId, cookieData] of Object.entries(data)) {
          if (cookieData && cookieData.valid) {
            store.connectServiceFromExtension(serviceId, cookieData);
          }
        }
      }

      if (event.data.type === 'COOKIE_UPDATE') {
        const { service, data } = event.data;
        store.connectServiceFromExtension(service, data);
      }
    };

    window.addEventListener('message', handleMessage);

    // Check if extension is installed
    window.postMessage({ type: 'GET_EXTENSION_STATUS' }, '*');

    // Timeout: if no response in 2s, assume extension not installed
    const timeout = setTimeout(() => {
      setExtensionLoading(false);
    }, 2000);

    return () => {
      window.removeEventListener('message', handleMessage);
      clearTimeout(timeout);
    };
  }, []);

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-3xl font-bold text-snow mb-2">Settings</h1>
        <p className="text-mist">Manage your connected services and preferences</p>
      </motion.div>

      {/* Extension Panel */}
      <ExtensionPanel
        detected={store.extension.detected}
        status={extensionStatus}
        loading={extensionLoading}
        onSyncAll={() => window.postMessage({ type: 'SYNC_ALL' }, '*')}
        onSyncService={(service) => window.postMessage({ type: 'SYNC_SERVICE', service }, '*')}
        onOpenLogin={(service) => window.postMessage({ type: 'OPEN_SERVICE_LOGIN', service }, '*')}
      />

      {/* Security notice */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="glass p-4 flex items-start gap-3 border border-rose/20"
      >
        <Shield className="w-5 h-5 text-rose flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-snow font-medium">Local storage only</p>
          <p className="text-xs text-mist mt-1">
            All tokens are stored in your browser's local storage. They never leave your device.
          </p>
        </div>
      </motion.div>

      {/* Service cards */}
      {services.map((service, i) => (
        <ServiceCard
          key={service.id}
          service={service}
          connected={store[service.id]?.connected}
          username={store[service.id]?.username}
          onConnect={(data) => {
            if (service.id === 'wetrakr') store.connectWeTrakr(data.username, data.accessToken, data.refreshToken);
            else if (service.id === 'trakt') store.connectTrakt(data.username, data.token, data.apiKey);
            else if (service.id === 'tmdb') store.connectTMDB(data.username, data.apiKey);
            else if (service.id === 'imdb') store.connectIMDb(data.sessionId, data.atMain, data.sessionToken, data.ubidMain, data.sessAtMain);
            else if (service.id === 'plex') store.connectPlex(data.username, data.token, data.baseUrl);
            else if (service.id === 'anilist') store.connectAniList(data.username, data.accessToken);
            else if (service.id === 'simkl') store.connectSimkl(data.username, data.accessToken, data.clientId);
            else if (service.id === 'jellyfin') store.connectJellyfin(data.username, data.apiKey, data.userId, data.baseUrl);
            else if (service.id === 'kodi') store.connectKodi(data.username, data.baseUrl);
          }}
          onDisconnect={() => store.disconnectService(service.id)}
          index={i}
        />
      ))}

      {/* Data management */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass-strong p-6"
      >
        <h3 className="font-display font-semibold text-snow mb-4">Data Management</h3>
        <div className="space-y-3">
          <button
            onClick={() => {
              if (confirm('Clear all local data? This cannot be undone.')) {
                localStorage.clear();
                window.location.reload();
              }
            }}
            className="w-full glass p-3 rounded-xl text-sm text-rose hover:bg-rose/10 transition-colors text-left"
          >
            Clear all local data
          </button>
        </div>
      </motion.div>
    </div>
  );
}

function ExtensionPanel({ detected, status, loading, onSyncAll, onSyncService, onOpenLogin }) {
  const [expanded, setExpanded] = useState(true);

  const services = [
    { id: 'imdb', name: 'IMDb', icon: 'IM', color: '#f5c518' },
    { id: 'letterboxd', name: 'Letterboxd', icon: 'LB', color: '#00e054' },
    { id: 'wetrakr', name: 'WeTrakr', icon: 'WT', color: '#6366f1' },
    { id: 'sofasidekick', name: 'Sofa Sidekick', icon: 'SS', color: '#f97316' },
  ];

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="glass-strong p-5"
      >
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-glow/30 border-t-glow rounded-full animate-spin" />
          <span className="text-sm text-mist">Checking for Chrome extension...</span>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 }}
      className={`glass-strong overflow-hidden ${detected ? 'border border-glow/30' : ''}`}
    >
      {/* Header */}
      <div
        className="p-5 flex items-center gap-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-glow to-purple-500 flex items-center justify-center">
          <Plug className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-display font-semibold text-snow">Chrome Extension</h3>
            {detected ? (
              <span className="flex items-center gap-1 text-xs bg-mint/20 text-mint px-2 py-0.5 rounded-full">
                <Check className="w-3 h-3" />
                Connected
              </span>
            ) : (
              <span className="flex items-center gap-1 text-xs bg-ghost text-mist px-2 py-0.5 rounded-full">
                <AlertTriangle className="w-3 h-3" />
                Not Installed
              </span>
            )}
          </div>
          <p className="text-sm text-mist mt-0.5">
            {detected
              ? 'Auto-sync cookies from your browser'
              : 'Install to auto-sync cookies from your browser'}
          </p>
        </div>
        <motion.div
          animate={{ rotate: expanded ? 180 : 0 }}
          className="text-mist"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </motion.div>
      </div>

      {/* Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-whisper"
          >
            {!detected ? (
              // Not installed state
              <div className="p-5 space-y-4">
                <p className="text-sm text-mist">
                  The StreamSyncr Chrome extension automatically extracts cookies from your browser
                  and syncs them with the app. No more manual cookie copying!
                </p>
                <div className="space-y-2">
                  <p className="text-xs text-mist font-medium uppercase tracking-wider">How to install:</p>
                  <ol className="text-sm text-mist space-y-1 list-decimal list-inside">
                    <li>Open Chrome and go to <code className="text-glow">chrome://extensions</code></li>
                    <li>Enable "Developer mode" (top right)</li>
                    <li>Click "Load unpacked" and select the <code className="text-glow">extension/</code> folder</li>
                    <li>Click the extension icon and connect your services</li>
                  </ol>
                </div>
                <a
                  href="https://github.com/djfulfill/StreamSyncr/tree/main/extension"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-glow hover:text-glow/80 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Download extension
                </a>
              </div>
            ) : (
              // Connected state
              <div className="p-5 space-y-4">
                <p className="text-sm text-mist">
                  Auto-sync is enabled. Cookies are extracted when you visit each service.
                </p>

                {/* Service status grid */}
                <div className="grid grid-cols-2 gap-3">
                  {services.map((svc) => {
                    const svcStatus = status?.services?.[svc.id];
                    const isValid = svcStatus?.valid || false;

                    return (
                      <div
                        key={svc.id}
                        className="p-3 rounded-xl bg-ghost flex items-center gap-3"
                      >
                        <div
                          className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-white"
                          style={{ background: svc.color }}
                        >
                          {svc.icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm text-snow font-medium">{svc.name}</div>
                          <div className={`text-xs ${isValid ? 'text-mint' : 'text-mist'}`}>
                            {isValid ? 'Synced' : 'Not synced'}
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (isValid) {
                              onSyncService(svc.id);
                            } else {
                              onOpenLogin(svc.id);
                            }
                          }}
                          className={`p-1.5 rounded-lg transition-colors ${
                            isValid
                              ? 'text-mint hover:bg-mint/10'
                              : 'text-mist hover:bg-ghost'
                          }`}
                          title={isValid ? 'Re-sync' : 'Open login page'}
                        >
                          {isValid ? (
                            <RefreshCw className="w-4 h-4" />
                          ) : (
                            <ExternalLink className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    );
                  })}
                </div>

                {/* Sync all button */}
                <button
                  onClick={onSyncAll}
                  className="w-full glass p-3 rounded-xl text-sm text-glow hover:bg-glow/10 transition-colors flex items-center justify-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Sync All Services
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function ServiceCard({ service, connected, username, onConnect, onDisconnect, index }) {
  const [expanded, setExpanded] = useState(false);
  const [showPasswords, setShowPasswords] = useState({});
  const [form, setForm] = useState({});

  const handleSubmit = (e) => {
    e.preventDefault();
    onConnect(form);
    setExpanded(false);
    setForm({});
  };

  const togglePassword = (key) => {
    setShowPasswords((p) => ({ ...p, [key]: !p[key] }));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 + index * 0.05 }}
      className={`glass-strong overflow-hidden ${connected ? 'border border-' + service.color + '/30' : ''}`}
    >
      {/* Header */}
      <div className="p-5 flex items-center gap-4">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${service.gradient} flex items-center justify-center`}>
          <span className="font-display font-bold text-void text-lg">{service.name[0]}</span>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-display font-semibold text-snow">{service.name}</h3>
            {connected && (
              <span className="flex items-center gap-1 text-xs bg-mint/20 text-mint px-2 py-0.5 rounded-full">
                <Check className="w-3 h-3" />
                Connected
              </span>
            )}
          </div>
          <p className="text-sm text-mist mt-0.5">{service.description}</p>
          {connected && <p className="text-xs text-mist mt-1">as {username}</p>}
        </div>
        <div className="flex gap-2">
          <a
            href={service.docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 glass rounded-lg text-mist hover:text-snow transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
          {connected ? (
            <motion.button
              onClick={onDisconnect}
              className="p-2 glass rounded-lg text-rose hover:bg-rose/10 transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <X className="w-4 h-4" />
            </motion.button>
          ) : (
            <motion.button
              onClick={() => setExpanded(!expanded)}
              className="bg-glow text-void font-semibold px-4 py-2 rounded-xl text-sm"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Connect
            </motion.button>
          )}
        </div>
      </div>

      {/* Connect form */}
      {expanded && !connected && (
        <motion.form
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          onSubmit={handleSubmit}
          className="border-t border-whisper p-5 space-y-4"
        >
          {service.fields.map((field) => (
            <div key={field.key}>
              <label className="block text-xs text-mist mb-1.5 font-medium">{field.label}</label>
              <div className="relative">
                <input
                  type={field.type === 'password' && !showPasswords[field.key] ? 'password' : 'text'}
                  value={form[field.key] || ''}
                  onChange={(e) => setForm((f) => ({ ...f, [field.key]: e.target.value }))}
                  className="w-full glass bg-transparent text-snow text-sm px-4 py-3 rounded-xl border-0 outline-none placeholder:text-whisper"
                  placeholder={`Enter ${field.label.toLowerCase()}`}
                  required
                />
                {field.type === 'password' && (
                  <button
                    type="button"
                    onClick={() => togglePassword(field.key)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-mist hover:text-snow"
                  >
                    {showPasswords[field.key] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                )}
              </div>
            </div>
          ))}
          <div className="flex gap-3 pt-2">
            <button type="submit" className="flex-1 bg-glow text-void font-semibold py-3 rounded-xl">
              Connect {service.name}
            </button>
            <button type="button" onClick={() => setExpanded(false)} className="glass text-mist px-6 py-3 rounded-xl">
              Cancel
            </button>
          </div>
        </motion.form>
      )}
    </motion.div>
  );
}
