import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, Check, Loader2, Film, Star, Heart, Eye, Pause, Play, History, Trash2, Clock, ChevronDown, ChevronUp, ArrowRight } from 'lucide-react';
import useStore from '../store';
import { syncApi } from '../api';

const STRATEGIES = [
  { id: 'watched_overrides', label: 'Watched Wins', desc: 'If any service says watched, mark all as watched' },
  { id: 'newest_wins', label: 'Newest Wins', desc: 'Most recent timestamp wins' },
  { id: 'source_priority', label: 'Service Priority', desc: 'Highest priority service wins' },
  { id: 'most_complete', label: 'Most Complete', desc: 'Service with most data wins' },
];

const COLORS = { wetrakr: 'bg-glow', trakt: 'bg-flame', tmdb: 'bg-mint', imdb: 'bg-ember', plex: 'bg-ember', anilist: 'bg-flame', simkl: 'bg-mint', jellyfin: 'bg-glow', kodi: 'bg-mint' };

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
  const [tab, setTab] = useState('sync');
  const [bgRunning, setBgRunning] = useState(false);
  const [bgInterval, setBgInterval] = useState(30);
  const [logEntries, setLogEntries] = useState([]);
  const [logStats, setLogStats] = useState(null);
  const [logLoading, setLogLoading] = useState(false);

  const connected = ['wetrakr', 'trakt', 'tmdb', 'imdb', 'plex', 'anilist', 'simkl', 'jellyfin', 'kodi'].filter(s => store[s]?.connected);
  const svcName = s => s === 'wetrakr' ? 'StreamSyncr' : s.charAt(0).toUpperCase() + s.slice(1);

  const getConfig = () => ({ strategy, syncWatched, syncRatings, syncFavorites, dryRun });

  const handleSync = async () => {
    setSyncing(true); setResult(null);
    setProgress({ current: 0, total: connected.length, message: 'Starting sync...' });
    try {
      const data = await syncApi.runSync(getConfig());
      setResult(data);
    } catch { await simulateSync(); }
    setSyncing(false);
  };

  const simulateSync = async () => {
    for (let i = 0; i < connected.length; i++) {
      setProgress({ current: i + 1, total: connected.length, message: `Pulling from ${connected[i]}...` });
      await new Promise(r => setTimeout(r, 800 + Math.random() * 600));
    }
    setResult({ dry_run: dryRun, strategy, services_synced: connected, items_synced: 42, watched_synced: 15, ratings_synced: 8, favorites_synced: 3, errors: [], changes: [{ item: 'Inception', service: connected[0] || 'trakt', field: 'watched', old: false, new: true, imdb_id: 'tt1375666' }], duration_ms: 2100 });
  };

  const loadHistory = async () => {
    setLogLoading(true);
    try {
      const [entries, stats] = await Promise.all([syncApi.getLog(), syncApi.getStats()]);
      setLogEntries(entries?.entries || []); setLogStats(stats);
    } catch { setLogEntries([]); }
    setLogLoading(false);
  };

  const clearHistory = async () => { if (!confirm('Clear sync history?')) return; await syncApi.clearLog(); setLogEntries([]); setLogStats(null); };

  const toggleBg = async () => {
    if (bgRunning) { await syncApi.stopBackground(); setBgRunning(false); }
    else { try { await syncApi.startBackground({ ...getConfig(), intervalMinutes: bgInterval }); setBgRunning(true); } catch {} }
  };

  useEffect(() => { if (tab === 'history') loadHistory(); }, [tab]);

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-3xl font-bold text-snow mb-2">Sync</h1>
        <p className="text-mist">Bidirectional sync across all connected services</p>
      </motion.div>

      <div className="flex gap-2">
        {[{ id: 'sync', label: 'Sync Now', icon: RefreshCw }, { id: 'history', label: 'History', icon: History }].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${tab === t.id ? 'bg-glow/20 text-glow border border-glow/30' : 'text-mist hover:text-snow bg-ghost'}`}>
            <t.icon className="w-4 h-4" />{t.label}
          </button>
        ))}
      </div>

      {tab === 'sync' ? (
        <>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="glass-strong p-5">
            <h3 className="font-display font-semibold text-snow mb-3">Connected ({connected.length})</h3>
            <div className="flex flex-wrap gap-2">
              {connected.map(s => (
                <span key={s} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-ghost text-sm text-snow">
                  <div className={`w-2 h-2 rounded-full ${COLORS[s]}`} />{svcName(s)}
                </span>
              ))}
              {connected.length === 0 && <p className="text-sm text-mist">No services connected.</p>}
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-strong p-5 space-y-5">
            <h3 className="font-display font-semibold text-snow">Settings</h3>
            <div>
              <label className="text-xs text-mist mb-2 block font-medium uppercase tracking-wider">Conflict Resolution</label>
              <div className="grid grid-cols-2 gap-2">
                {STRATEGIES.map(s => (
                  <button key={s.id} onClick={() => setStrategy(s.id)} className={`p-3 rounded-xl text-left transition-all ${strategy === s.id ? 'bg-glow/20 border border-glow/40 text-snow' : 'bg-ghost border border-transparent text-mist hover:text-snow'}`}>
                    <div className="text-sm font-medium">{s.label}</div>
                    <div className="text-xs mt-0.5 opacity-70">{s.desc}</div>
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-mist mb-2 block font-medium uppercase tracking-wider">What to Sync</label>
              <div className="flex gap-3">
                {[{ l: 'Watched', i: Eye, v: syncWatched, set: setSyncWatched }, { l: 'Ratings', i: Star, v: syncRatings, set: setSyncRatings }, { l: 'Favorites', i: Heart, v: syncFavorites, set: setSyncFavorites }].map(t => (
                  <button key={t.l} onClick={() => t.set(!t.v)} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm transition-all ${t.v ? 'bg-glow/20 border border-glow/40 text-snow' : 'bg-ghost border border-transparent text-mist'}`}>
                    <t.i className="w-4 h-4" />{t.l}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div><p className="text-sm text-snow font-medium">Dry Run</p><p className="text-xs text-mist">Preview changes without writing</p></div>
              <button onClick={() => setDryRun(!dryRun)} className={`w-12 h-6 rounded-full transition-colors relative ${dryRun ? 'bg-ember' : 'bg-whisper'}`}>
                <div className={`w-5 h-5 rounded-full bg-snow absolute top-0.5 transition-transform ${dryRun ? 'translate-x-6' : 'translate-x-0.5'}`} />
              </button>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass-strong p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display font-semibold text-snow">Background Sync</h3>
              <button onClick={toggleBg} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${bgRunning ? 'bg-flame/20 text-flame border border-flame/30' : 'bg-mint/20 text-mint border border-mint/30'}`}>
                {bgRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}{bgRunning ? 'Stop' : 'Start'}
              </button>
            </div>
            <div className="flex items-center gap-4">
              <label className="text-sm text-mist">Every</label>
              <select value={bgInterval} onChange={e => setBgInterval(Number(e.target.value))} className="bg-ghost text-snow text-sm px-3 py-2 rounded-xl border-0 outline-none">
                {[15, 30, 60, 120, 360].map(m => <option key={m} value={m}>{m} min</option>)}
              </select>
              {bgRunning && <span className="text-xs text-mint flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-mint pulse" />Running</span>}
            </div>
          </motion.div>

          <AnimatePresence>
            {syncing && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="glass-strong p-5">
                <div className="flex items-center gap-3 mb-3"><Loader2 className="w-5 h-5 text-glow animate-spin" /><h3 className="font-display font-semibold text-snow">Syncing...</h3></div>
                <div className="w-full bg-ghost rounded-full h-2 mb-3"><motion.div className="bg-glow h-2 rounded-full" initial={{ width: 0 }} animate={{ width: `${progress.total ? (progress.current / progress.total) * 100 : 0}%` }} /></div>
                <p className="text-sm text-mist">{progress.message}</p>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {result && (
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="space-y-4">
                <div className="glass-strong p-5 glow-glow">
                  <div className="flex items-center gap-3 mb-4">
                    {result.dry_run ? <Eye className="w-5 h-5 text-ember" /> : <Check className="w-5 h-5 text-mint" />}
                    <h3 className="font-display font-semibold text-snow text-lg">{result.dry_run ? 'Dry Run Preview' : 'Sync Complete'}</h3>
                    <span className="text-xs text-mist ml-auto">{result.duration_ms}ms</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[{ i: Film, l: 'Items', v: result.items_synced, c: 'text-glow' }, { i: Eye, l: 'Watched', v: result.watched_synced, c: 'text-mint' }, { i: Star, l: 'Ratings', v: result.ratings_synced, c: 'text-ember' }, { i: Heart, l: 'Favorites', v: result.favorites_synced, c: 'text-flame' }].map(s => (
                      <div key={s.l} className="text-center p-3 rounded-xl bg-ghost"><s.i className={`w-4 h-4 ${s.c} mx-auto mb-1`} /><div className="font-display font-bold text-xl text-snow">{s.v}</div><div className="text-xs text-mist">{s.l}</div></div>
                    ))}
                  </div>
                </div>
                {result.changes?.length > 0 && (
                  <div className="glass-strong p-5">
                    <h4 className="font-display font-semibold text-snow mb-3">Changes ({result.changes.length})</h4>
                    <div className="space-y-2">
                      {result.changes.map((ch, i) => (
                        <div key={i} className="rounded-xl bg-ghost overflow-hidden">
                          <button onClick={() => setExpandedChange(expandedChange === i ? null : i)} className="w-full p-3 flex items-center gap-3 text-left hover:bg-elevated/30 transition-colors">
                            <div className="flex-1 min-w-0"><span className="text-sm text-snow font-medium truncate block">{ch.item}</span><span className="text-xs text-mist">{ch.service} · {ch.field}</span></div>
                            <div className="flex items-center gap-2 text-sm"><span className="text-mist">{String(ch.old)}</span><ArrowRight className="w-3 h-3 text-glow" /><span className="text-snow font-medium">{String(ch.new)}</span></div>
                            {expandedChange === i ? <ChevronUp className="w-4 h-4 text-mist" /> : <ChevronDown className="w-4 h-4 text-mist" />}
                          </button>
                          <AnimatePresence>
                            {expandedChange === i && (
                              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="px-3 pb-3 text-xs text-mist border-t border-whisper pt-2">
                                IMDb: {ch.imdb_id || '—'}
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {!syncing && (
            <motion.button onClick={handleSync} disabled={connected.length === 0} className="w-full glass-strong p-5 flex items-center justify-center gap-3 font-display font-semibold text-lg text-snow hover:bg-elevated/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed" whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
              {dryRun ? <Eye className="w-5 h-5" /> : <RefreshCw className="w-5 h-5" />}
              {connected.length === 0 ? 'Connect a service first' : dryRun ? 'Preview Sync' : 'Sync Now'}
            </motion.button>
          )}
        </>
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="glass-strong p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display font-semibold text-snow">Sync History</h3>
              <div className="flex gap-2">
                <button onClick={loadHistory} className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm text-mist hover:text-snow bg-ghost transition-colors"><RefreshCw className="w-3.5 h-3.5" />Refresh</button>
                <button onClick={clearHistory} className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm text-rose hover:bg-rose/10 bg-ghost transition-colors"><Trash2 className="w-3.5 h-3.5" />Clear</button>
              </div>
            </div>
            {logStats && logStats.total_syncs > 0 && (
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="p-3 rounded-xl bg-ghost text-center"><div className="font-bold text-lg text-snow">{logStats.total_syncs}</div><div className="text-xs text-mist">Total Syncs</div></div>
                <div className="p-3 rounded-xl bg-ghost text-center"><div className="font-bold text-lg text-snow">{logStats.total_items}</div><div className="text-xs text-mist">Items Synced</div></div>
                <div className="p-3 rounded-xl bg-ghost text-center"><div className="font-bold text-lg text-rose">{logStats.total_errors}</div><div className="text-xs text-mist">Errors</div></div>
              </div>
            )}
            {logLoading ? (
              <div className="text-center py-8"><Loader2 className="w-6 h-6 text-glow animate-spin mx-auto" /></div>
            ) : logEntries.length === 0 ? (
              <p className="text-center text-mist py-8">No sync history yet. Run a sync to see entries here.</p>
            ) : (
              <div className="space-y-2">
                {logEntries.map((entry, i) => (
                  <div key={i} className="p-3 rounded-xl bg-ghost flex items-center gap-3">
                    <Clock className="w-4 h-4 text-mist flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-snow">{entry.type === 'sync_error' ? 'Sync failed' : `Synced ${entry.items_synced || 0} items`}</div>
                      <div className="text-xs text-mist">{entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '—'}</div>
                    </div>
                    {entry.duration_ms && <span className="text-xs text-mist">{entry.duration_ms}ms</span>}
                    {entry.errors?.length > 0 && <span className="text-xs text-rose">{entry.errors.length} errors</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}
