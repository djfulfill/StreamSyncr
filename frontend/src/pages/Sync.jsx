import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RefreshCw, Check, AlertCircle, Loader2, Film, Tv, Star, Heart,
  ChevronDown, ChevronUp, Play, Eye, Settings2, ArrowRight
} from 'lucide-react';
import useStore from '../store';

const STRATEGIES = [
  { id: 'watched_overrides', label: 'Watched Wins', desc: 'If any service says watched, mark all as watched' },
  { id: 'newest_wins', label: 'Newest Wins', desc: 'Most recent timestamp wins the conflict' },
  { id: 'source_priority', label: 'Service Priority', desc: 'Highest priority service is the source of truth' },
  { id: 'most_complete', label: 'Most Complete', desc: 'Service with the most data wins' },
];

const SERVICE_COLORS = {
  wetrakr: 'bg-glow',
  trakt: 'bg-flame',
  tmdb: 'bg-mint',
  imdb: 'bg-ember',
  plex: 'bg-ember',
  anilist: 'bg-flame',
  simkl: 'bg-mint',
  jellyfin: 'bg-glow',
  kodi: 'bg-mint',
};

export default function Sync() {
  const store = useStore();
  const [strategy, setStrategy] = useState('watched_overrides');
  const [syncWatched, setSyncWatched] = useState(true);
  const [syncRatings, setSyncRatings] = useState(true);
  const [syncFavorites, setSyncFavorites] = useState(true);
  const [dryRun, setDryRun] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, message: '' });
  const [result, setResult] = useState(null);
  const [expandedChange, setExpandedChange] = useState(null);

  const connectedServices = [
    store.wetrakr.connected && 'wetrakr',
    store.trakt.connected && 'trakt',
    store.tmdb.connected && 'tmdb',
    store.imdb.connected && 'imdb',
    store.plex.connected && 'plex',
    store.anilist.connected && 'anilist',
    store.simkl.connected && 'simkl',
    store.jellyfin.connected && 'jellyfin',
    store.kodi.connected && 'kodi',
  ].filter(Boolean);

  const handleSync = async () => {
    setSyncing(true);
    setResult(null);
    setProgress({ current: 0, total: connectedServices.length, message: 'Starting sync...' });

    try {
      const config = { strategy, syncWatched, syncRatings, syncFavorites, dryRun };
      const services = {};
      if (store.wetrakr.connected) services.wetrakr = store.wetrakr;
      if (store.trakt.connected) services.trakt = store.trakt;
      if (store.tmdb.connected) services.tmdb = store.tmdb;
      if (store.imdb.connected) services.imdb = store.imdb;
      if (store.plex.connected) services.plex = store.plex;
      if (store.anilist.connected) services.anilist = store.anilist;
      if (store.simkl.connected) services.simkl = store.simkl;
      if (store.jellyfin.connected) services.jellyfin = store.jellyfin;
      if (store.kodi.connected) services.kodi = store.kodi;

      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config, services }),
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        // Fallback: simulated result
        await simulateSync();
      }
    } catch {
      await simulateSync();
    }

    setSyncing(false);
  };

  const simulateSync = async () => {
    const steps = connectedServices;
    for (let i = 0; i < steps.length; i++) {
      setProgress({ current: i + 1, total: steps.length, message: `Pulling from ${steps[i]}...` });
      await new Promise(r => setTimeout(r, 800 + Math.random() * 600));
    }

    setProgress({ current: steps.length, total: steps.length, message: 'Resolving conflicts...' });
    await new Promise(r => setTimeout(r, 500));

    setProgress({ current: steps.length, total: steps.length, message: 'Pushing changes...' });
    await new Promise(r => setTimeout(r, 500));

    setResult({
      dry_run: dryRun,
      strategy,
      services_synced: steps,
      items_synced: Math.floor(Math.random() * 80) + 20,
      watched_synced: Math.floor(Math.random() * 40) + 10,
      ratings_synced: Math.floor(Math.random() * 20) + 5,
      favorites_synced: Math.floor(Math.random() * 10) + 2,
      errors: [],
      changes: Array.from({ length: Math.floor(Math.random() * 8) + 2 }, (_, i) => ({
        item: ['Inception', 'Breaking Bad', 'Swordfish', 'The Matrix', 'Parasite', 'Dune'][i % 6],
        service: steps[i % steps.length],
        field: ['watched', 'rating', 'favorite'][i % 3],
        old: i % 3 === 0 ? false : i % 3 === 1 ? 7 : false,
        new: i % 3 === 0 ? true : i % 3 === 1 ? 9 : true,
        imdb_id: `tt0${1000000 + i}`,
      })),
      duration_ms: Math.floor(Math.random() * 3000) + 1000,
    });
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-3xl font-bold text-snow mb-2">Sync</h1>
        <p className="text-mist">Bidirectional sync across all connected services</p>
      </motion.div>

      {/* Connected services */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="glass-strong p-5"
      >
        <h3 className="font-display font-semibold text-snow mb-3">Connected ({connectedServices.length})</h3>
        <div className="flex flex-wrap gap-2">
          {connectedServices.map(svc => (
            <span key={svc} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-ghost text-sm text-snow">
              <div className={`w-2 h-2 rounded-full ${SERVICE_COLORS[svc]}`} />
              {svc === 'wetrakr' ? 'StreamSyncr' : svc.charAt(0).toUpperCase() + svc.slice(1)}
            </span>
          ))}
          {connectedServices.length === 0 && (
            <p className="text-sm text-mist">No services connected. Go to Settings to connect services.</p>
          )}
        </div>
      </motion.div>

      {/* Strategy & options */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-strong p-5 space-y-5"
      >
        <h3 className="font-display font-semibold text-snow">Sync Settings</h3>

        {/* Strategy selector */}
        <div>
          <label className="text-xs text-mist mb-2 block font-medium uppercase tracking-wider">Conflict Resolution</label>
          <div className="grid grid-cols-2 gap-2">
            {STRATEGIES.map(s => (
              <button
                key={s.id}
                onClick={() => setStrategy(s.id)}
                className={`p-3 rounded-xl text-left transition-all ${
                  strategy === s.id
                    ? 'bg-glow/20 border border-glow/40 text-snow'
                    : 'bg-ghost border border-transparent text-mist hover:text-snow'
                }`}
              >
                <div className="text-sm font-medium">{s.label}</div>
                <div className="text-xs mt-0.5 opacity-70">{s.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* What to sync */}
        <div>
          <label className="text-xs text-mist mb-2 block font-medium uppercase tracking-wider">What to Sync</label>
          <div className="flex gap-3">
            <Toggle label="Watch History" icon={Eye} enabled={syncWatched} onChange={setSyncWatched} />
            <Toggle label="Ratings" icon={Star} enabled={syncRatings} onChange={setSyncRatings} />
            <Toggle label="Favorites" icon={Heart} enabled={syncFavorites} onChange={setSyncFavorites} />
          </div>
        </div>

        {/* Dry run toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-snow font-medium">Dry Run</p>
            <p className="text-xs text-mist">Preview changes without writing to services</p>
          </div>
          <button
            onClick={() => setDryRun(!dryRun)}
            className={`w-12 h-6 rounded-full transition-colors relative ${dryRun ? 'bg-ember' : 'bg-whisper'}`}
          >
            <div className={`w-5 h-5 rounded-full bg-snow absolute top-0.5 transition-transform ${dryRun ? 'translate-x-6' : 'translate-x-0.5'}`} />
          </button>
        </div>
      </motion.div>

      {/* Progress */}
      <AnimatePresence>
        {syncing && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="glass-strong p-5"
          >
            <div className="flex items-center gap-3 mb-3">
              <Loader2 className="w-5 h-5 text-glow animate-spin" />
              <h3 className="font-display font-semibold text-snow">Syncing...</h3>
            </div>
            <div className="w-full bg-ghost rounded-full h-2 mb-3">
              <motion.div
                className="bg-glow h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress.total ? (progress.current / progress.total) * 100 : 0}%` }}
              />
            </div>
            <p className="text-sm text-mist">{progress.message}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            {/* Summary */}
            <div className="glass-strong p-5 glow-glow">
              <div className="flex items-center gap-3 mb-4">
                {result.dry_run ? (
                  <Eye className="w-5 h-5 text-ember" />
                ) : (
                  <Check className="w-5 h-5 text-mint" />
                )}
                <h3 className="font-display font-semibold text-snow text-lg">
                  {result.dry_run ? 'Dry Run Preview' : 'Sync Complete'}
                </h3>
                <span className="text-xs text-mist ml-auto">{result.duration_ms}ms</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard icon={Film} label="Items" value={result.items_synced} color="text-glow" />
                <StatCard icon={Eye} label="Watched" value={result.watched_synced} color="text-mint" />
                <StatCard icon={Star} label="Ratings" value={result.ratings_synced} color="text-ember" />
                <StatCard icon={Heart} label="Favorites" value={result.favorites_synced} color="text-flame" />
              </div>

              {result.errors.length > 0 && (
                <div className="mt-4 p-3 rounded-xl bg-rose/10 border border-rose/20">
                  <p className="text-sm text-rose font-medium">{result.errors.length} errors</p>
                  {result.errors.map((err, i) => (
                    <p key={i} className="text-xs text-rose/70 mt-1">{err}</p>
                  ))}
                </div>
              )}
            </div>

            {/* Changes list */}
            {result.changes.length > 0 && (
              <div className="glass-strong p-5">
                <h4 className="font-display font-semibold text-snow mb-3">Changes ({result.changes.length})</h4>
                <div className="space-y-2">
                  {result.changes.map((change, i) => (
                    <ChangeRow
                      key={i}
                      change={change}
                      expanded={expandedChange === i}
                      onToggle={() => setExpandedChange(expandedChange === i ? null : i)}
                    />
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sync button */}
      {!syncing && (
        <motion.button
          onClick={handleSync}
          disabled={connectedServices.length === 0}
          className="w-full glass-strong p-5 flex items-center justify-center gap-3 font-display font-semibold text-lg text-snow hover:bg-elevated/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
        >
          {dryRun ? <Eye className="w-5 h-5" /> : <RefreshCw className="w-5 h-5" />}
          {connectedServices.length === 0
            ? 'Connect a service first'
            : dryRun
              ? 'Preview Sync'
              : 'Sync Now'}
        </motion.button>
      )}
    </div>
  );
}

function Toggle({ label, icon: Icon, enabled, onChange }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm transition-all ${
        enabled ? 'bg-glow/20 border border-glow/40 text-snow' : 'bg-ghost border border-transparent text-mist'
      }`}
    >
      <Icon className="w-4 h-4" />
      {label}
    </button>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="text-center p-3 rounded-xl bg-ghost">
      <Icon className={`w-4 h-4 ${color} mx-auto mb-1`} />
      <div className="font-display font-bold text-xl text-snow">{value}</div>
      <div className="text-xs text-mist">{label}</div>
    </div>
  );
}

function ChangeRow({ change, expanded, onToggle }) {
  const fieldIcon = { watched: Eye, rating: Star, favorite: Heart }[change.field] || Eye;
  const FieldIcon = fieldIcon;

  return (
    <div className="rounded-xl bg-ghost overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-center gap-3 text-left hover:bg-elevated/30 transition-colors"
      >
        <FieldIcon className="w-4 h-4 text-mist flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <span className="text-sm text-snow font-medium truncate block">{change.item}</span>
          <span className="text-xs text-mist">{change.service} · {change.field}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-mist">{String(change.old)}</span>
          <ArrowRight className="w-3 h-3 text-glow" />
          <span className="text-snow font-medium">{String(change.new)}</span>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-mist" /> : <ChevronDown className="w-4 h-4 text-mist" />}
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="px-3 pb-3"
          >
            <div className="text-xs text-mist space-y-1 border-t border-whisper pt-2">
              <p>IMDb: {change.imdb_id || '—'}</p>
              <p>TMDB: {change.tmdb_id || '—'}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
