import { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Check, X, ExternalLink, Eye, EyeOff, Shield, Key, User } from 'lucide-react';
import useStore from '../store';

const services = [
  {
    id: 'wetrakr',
    name: 'StreamSyncr',
    description: 'Reverse-engineered API. Tokens expire after ~2 days.',
    color: 'glow',
    gradient: 'from-glow to-[#a29bfe]',
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
    color: 'flame',
    gradient: 'from-flame to-[#c0392b]',
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
    color: 'mint',
    gradient: 'from-mint to-[#00b859]',
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
    color: 'ember',
    gradient: 'from-ember to-[#d4a80a]',
    fields: [
      { key: 'sessionId', label: 'Session ID (session-id)', type: 'password' },
      { key: 'atMain', label: 'AT Main (at-main)', type: 'password' },
      { key: 'sessionToken', label: 'Session Token', type: 'password' },
      { key: 'ubidMain', label: 'UBID Main (optional)', type: 'password' },
      { key: 'sessAtMain', label: 'Sess AT Main (optional)', type: 'password' },
    ],
    docsUrl: 'https://www.imdb.com',
  },
];

export default function Settings() {
  const store = useStore();

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-3xl font-bold text-snow mb-2">Settings</h1>
        <p className="text-mist">Manage your connected services and preferences</p>
      </motion.div>

      {/* Security notice */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="glass p-4 flex items-start gap-3 border border-mint/20"
      >
        <Shield className="w-5 h-5 text-mint flex-shrink-0 mt-0.5" />
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
            if (service.id === 'wetrakr') {
              store.connectWeTrakr(data.username, data.accessToken, data.refreshToken);
            } else if (service.id === 'trakt') {
              store.connectTrakt(data.username, data.token, data.apiKey);
            } else if (service.id === 'tmdb') {
              store.connectTMDB(data.username, data.apiKey);
            }
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
                <Check className="w-3 h-3" /> Connected
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
            <button
              type="submit"
              className="flex-1 bg-glow text-void font-semibold py-3 rounded-xl"
            >
              Connect {service.name}
            </button>
            <button
              type="button"
              onClick={() => setExpanded(false)}
              className="glass text-mist px-6 py-3 rounded-xl"
            >
              Cancel
            </button>
          </div>
        </motion.form>
      )}
    </motion.div>
  );
}
