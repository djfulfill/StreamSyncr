import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Film, Tv, Grid3X3, List, Filter, SlidersHorizontal } from 'lucide-react';
import useStore from '../store';
import PosterCard from '../components/PosterCard';

const tabs = [
  { id: 'all', label: 'All', icon: Grid3X3 },
  { id: 'movies', label: 'Movies', icon: Film },
  { id: 'shows', label: 'TV Shows', icon: Tv },
];

const sortOptions = [
  { id: 'recent', label: 'Recently Added' },
  { id: 'title', label: 'Title A-Z' },
  { id: 'rating', label: 'Rating' },
  { id: 'year', label: 'Year' },
];

export default function Library() {
  const { library } = useStore();
  const [activeTab, setActiveTab] = useState('all');
  const [sortBy, setSortBy] = useState('recent');
  const [viewMode, setViewMode] = useState('grid');

  const filtered = library.filter((item) => {
    if (activeTab === 'movies') return item.media_type === 'movie' || !item.first_air_date;
    if (activeTab === 'shows') return item.media_type === 'tv' || item.first_air_date;
    return true;
  });

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'title') return (a.title || a.name).localeCompare(b.title || b.name);
    if (sortBy === 'rating') return (b.vote_average || 0) - (a.vote_average || 0);
    if (sortBy === 'year') return (b.release_date || '').localeCompare(a.release_date || '');
    return 0;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="font-display text-3xl font-bold text-snow">Your Library</h1>
          <p className="text-mist mt-1">{sorted.length} titles</p>
        </div>

        <div className="flex items-center gap-3">
          {/* View toggle */}
          <div className="glass flex items-center p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-glow/20 text-glow' : 'text-mist'}`}
            >
              <Grid3X3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-glow/20 text-glow' : 'text-mist'}`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="glass bg-transparent text-sm text-snow px-3 py-2 rounded-xl border-0 outline-none cursor-pointer"
          >
            {sortOptions.map((opt) => (
              <option key={opt.id} value={opt.id} className="bg-deep">
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-2">
        {tabs.map(({ id, label, icon: Icon }) => (
          <motion.button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === id
                ? 'bg-glow/20 text-glow border border-glow/30'
                : 'glass text-mist hover:text-snow'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Icon className="w-4 h-4" />
            {label}
          </motion.button>
        ))}
      </div>

      {/* Grid / List */}
      <AnimatePresence mode="wait">
        {sorted.length > 0 ? (
          viewMode === 'grid' ? (
            <motion.div
              key="grid"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4"
            >
              {sorted.map((item, i) => (
                <PosterCard key={item.id} item={item} index={i} />
              ))}
            </motion.div>
          ) : (
            <motion.div
              key="list"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-2"
            >
              {sorted.map((item, i) => (
                <ListItem key={item.id} item={item} index={i} />
              ))}
            </motion.div>
          )
        ) : (
          <EmptyState />
        )}
      </AnimatePresence>
    </div>
  );
}

function ListItem({ item, index }) {
  const title = item.title || item.name;
  const year = item.release_date?.substring(0, 4) || item.first_air_date?.substring(0, 4);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
      className="glass flex items-center gap-4 p-3 hover:bg-elevated/30 transition-colors cursor-pointer"
    >
      <img
        src={item.poster_path ? `https://image.tmdb.org/t/p/w92${item.poster_path}` : null}
        alt={title}
        className="w-12 h-16 object-cover rounded-lg bg-deep"
      />
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-snow truncate">{title}</h3>
        <p className="text-sm text-mist">{year}</p>
      </div>
      {item.vote_average > 0 && (
        <span className="text-sm font-bold text-ember">{item.vote_average.toFixed(1)}</span>
      )}
    </motion.div>
  );
}

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-strong p-16 text-center"
    >
      <Film className="w-16 h-16 text-whisper mx-auto mb-4" />
      <h3 className="font-display text-xl font-semibold text-snow mb-2">Your library is empty</h3>
      <p className="text-mist max-w-md mx-auto">
        Connect your streaming services and sync your watch history to see your titles here.
      </p>
    </motion.div>
  );
}
