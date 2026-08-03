import { useState } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, ArrowRight, Check, AlertCircle, Loader2, Film, Tv, Clock } from 'lucide-react';
import useStore from '../store';

const syncSteps = [
  { id: 'wetrakr', label: 'Fetch from WeTrakr', service: 'wetrakr' },
  { id: 'trakt', label: 'Fetch from Trakt', service: 'trakt' },
  { id: 'tmdb', label: 'Enrich with TMDB', service: 'tmdb' },
  { id: 'merge', label: 'Merge & deduplicate', service: null },
  { id: 'push', label: 'Push to target services', service: null },
];

export default function Sync() {
  const { wetrakr, trakt, tmdb: tmdbState, setLibrary, setSyncStatus } = useStore();
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState({});
  const [results, setResults] = useState(null);

  const connectedServices = [
    wetrakr.connected && 'WeTrakr',
    trakt.connected && 'Trakt',
    tmdbState.connected && 'TMDB',
  ].filter(Boolean);

  const handleSync = async () => {
    setSyncing(true);
    setProgress({});
    setResults(null);

    // Simulate sync steps
    for (const step of syncSteps) {
      if (step.service && !useStore.getState()[step.service]?.connected) {
        setProgress((p) => ({ ...p, [step.id]: 'skipped' }));
        continue;
      }

      setProgress((p) => ({ ...p, [step.id]: 'running' }));
      await new Promise((r) => setTimeout(r, 1500 + Math.random() * 1000));
      setProgress((p) => ({ ...p, [step.id]: 'done' }));
    }

    // Simulate merge results
    setResults({
      movies: Math.floor(Math.random() * 50) + 20,
      shows: Math.floor(Math.random() * 30) + 10,
      synced: Math.floor(Math.random() * 100) + 50,
      conflicts: Math.floor(Math.random() * 5),
    });

    setSyncing(false);
    setSyncStatus('idle');
  };

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-3xl font-bold text-snow mb-2">Sync Library</h1>
        <p className="text-mist">Merge your watch history across all connected services</p>
      </motion.div>

      {/* Service summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-strong p-6"
      >
        <h3 className="font-display font-semibold text-snow mb-4">Connected Services</h3>
        <div className="grid grid-cols-3 gap-4">
          <ServiceStatus name="WeTrakr" connected={wetrakr.connected} username={wetrakr.username} />
          <ServiceStatus name="Trakt" connected={trakt.connected} username={trakt.username} />
          <ServiceStatus name="TMDB" connected={tmdbState.connected} username={tmdbState.username} />
        </div>
      </motion.div>

      {/* Sync progress */}
      {syncing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-strong p-6"
        >
          <h3 className="font-display font-semibold text-snow mb-4">Syncing...</h3>
          <div className="space-y-3">
            {syncSteps.map((step, i) => (
              <StepRow key={step.id} step={step} status={progress[step.id]} index={i} />
            ))}
          </div>
        </motion.div>
      )}

      {/* Results */}
      {results && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-strong p-6 glow-glow"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-mint/20 flex items-center justify-center">
              <Check className="w-5 h-5 text-mint" />
            </div>
            <h3 className="font-display font-semibold text-snow text-lg">Sync Complete!</h3>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <ResultCard icon={Film} label="Movies" value={results.movies} color="text-glow" />
            <ResultCard icon={Tv} label="Shows" value={results.shows} color="text-ember" />
            <ResultCard icon={RefreshCw} label="Synced" value={results.synced} color="text-mint" />
            <ResultCard icon={AlertCircle} label="Conflicts" value={results.conflicts} color="text-rose" />
          </div>
        </motion.div>
      )}

      {/* Sync button */}
      {!syncing && (
        <motion.button
          onClick={handleSync}
          disabled={connectedServices.length === 0}
          className="w-full glass-strong p-5 flex items-center justify-center gap-3 font-display font-semibold text-lg text-snow hover:bg-elevated/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
        >
          <RefreshCw className="w-5 h-5" />
          {connectedServices.length === 0 ? 'Connect a service first' : 'Sync Now'}
        </motion.button>
      )}
    </div>
  );
}

function ServiceStatus({ name, connected, username }) {
  return (
    <div className={`p-4 rounded-xl border ${connected ? 'border-mint/30 bg-mint/5' : 'border-whisper bg-ghost'}`}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${connected ? 'bg-mint pulse' : 'bg-whisper'}`} />
        <span className="font-medium text-snow text-sm">{name}</span>
      </div>
      <p className="text-xs text-mist">{connected ? username : 'Not connected'}</p>
    </div>
  );
}

function StepRow({ step, status, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="flex items-center gap-3"
    >
      {status === 'done' ? (
        <div className="w-6 h-6 rounded-full bg-mint/20 flex items-center justify-center flex-shrink-0">
          <Check className="w-3.5 h-3.5 text-mint" />
        </div>
      ) : status === 'skipped' ? (
        <div className="w-6 h-6 rounded-full bg-whisper flex items-center justify-center flex-shrink-0">
          <span className="text-[10px] text-mist">-</span>
        </div>
      ) : status === 'running' ? (
        <Loader2 className="w-5 h-5 text-glow animate-spin flex-shrink-0" />
      ) : (
        <div className="w-6 h-6 rounded-full border border-whisper flex-shrink-0" />
      )}
      <span className={`text-sm ${status === 'done' ? 'text-snow' : status === 'skipped' ? 'text-whisper' : 'text-mist'}`}>
        {step.label}
      </span>
      {status === 'skipped' && (
        <span className="text-[10px] text-whisper ml-auto">not connected</span>
      )}
    </motion.div>
  );
}

function ResultCard({ icon: Icon, label, value, color }) {
  return (
    <div className="text-center p-4 rounded-xl bg-ghost">
      <Icon className={`w-5 h-5 ${color} mx-auto mb-2`} />
      <div className="font-display font-bold text-2xl text-snow">{value}</div>
      <div className="text-xs text-mist">{label}</div>
    </div>
  );
}
