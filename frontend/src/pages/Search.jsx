import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search as SearchIcon, Loader2, Film, Tv } from 'lucide-react';
import useStore from '../store';
import PosterCard from '../components/PosterCard';
import { tmdb as tmdbApi } from '../api';

export default function Search() {
  const { tmdb: tmdbState, trakt: traktState } = useStore();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      if (tmdbState.connected && tmdbState.apiKey) {
        const data = await tmdbApi.search(query, tmdbState.apiKey);
        setResults(data.results || []);
      }
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  }, [query, tmdbState]);

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-3xl font-bold text-snow mb-6">Search</h1>

        {/* Search bar */}
        <div className="relative">
          <SearchIcon className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-mist" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search movies, TV shows..."
            className="w-full glass-strong bg-transparent text-snow text-lg pl-14 pr-32 py-5 rounded-2xl border-0 outline-none placeholder:text-whisper"
          />
          <motion.button
            onClick={handleSearch}
            className="absolute right-3 top-1/2 -translate-y-1/2 bg-glow text-void font-semibold px-6 py-2.5 rounded-xl"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Search
          </motion.button>
        </div>

        {/* Source indicator */}
        <div className="flex gap-2 mt-4">
          <span className="text-xs text-mist">Searching via:</span>
          {tmdbState.connected && <span className="text-xs bg-flame/20 text-flame px-2 py-0.5 rounded-full">TMDB</span>}
          {!tmdbState.connected && <span className="text-xs text-whisper">No services connected</span>}
        </div>
      </motion.div>

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-glow animate-spin" />
        </div>
      ) : searched && results.length === 0 ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-strong p-16 text-center">
          <SearchIcon className="w-16 h-16 text-whisper mx-auto mb-4" />
          <h3 className="font-display text-xl font-semibold text-snow mb-2">No results found</h3>
          <p className="text-mist">Try a different search term</p>
        </motion.div>
      ) : results.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {results.map((item, i) => (
            <PosterCard key={item.id} item={item} index={i} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
