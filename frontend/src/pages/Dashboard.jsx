import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Film, TrendingUp, Clock, Star, Tv, ArrowRight, Zap } from 'lucide-react';
import useStore from '../store';
import PosterCard from '../components/PosterCard';
import { tmdb, tmdbBackdrop } from '../api';

export default function Dashboard() {
  const { wetrakr, trakt, tmdb: tmdbState, library } = useStore();
  const [trending, setTrending] = useState([]);
  const [popular, setPopular] = useState([]);
  const [stats, setStats] = useState({ movies: 0, shows: 0, hours: 0 });

  useEffect(() => {
    if (tmdbState.connected && tmdbState.apiKey) {
      tmdb.trending(tmdbState.apiKey).then((data) => setTrending(data.results?.slice(0, 10) || []));
      tmdb.popular(tmdbState.apiKey).then((data) => setPopular(data.results?.slice(0, 10) || []));
    }
  }, [tmdbState.connected]);

  useEffect(() => {
    const movies = library.filter((i) => i.media_type === 'movie' || !i.first_air_date).length;
    const shows = library.filter((i) => i.media_type === 'tv' || i.first_air_date).length;
    setStats({ movies, shows, hours: movies * 2 + shows * 8 });
  }, [library]);

  const connectedCount = [wetrakr.connected, trakt.connected, tmdbState.connected].filter(Boolean).length;

  return (
    <div className="space-y-8">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl glass-strong p-8 lg:p-12"
      >
        <div className="absolute inset-0 opacity-20">
          {trending[0]?.backdrop_path && (
            <img
              src={tmdbBackdrop(trending[0].backdrop_path)}
              alt=""
              className="w-full h-full object-cover"
            />
          )}
          <div className="absolute inset-0 bg-gradient-to-r from-void via-void/80 to-transparent" />
        </div>

        <div className="relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h1 className="font-display text-4xl lg:text-5xl font-bold tracking-tight mb-3">
              Welcome to{' '}
              <span className="bg-gradient-to-r from-glow via-ember to-rose bg-clip-text text-transparent">
                StreamSync
              </span>
            </h1>
            <p className="text-mist text-lg max-w-xl">
              Your unified streaming tracker. Connect services, sync your library, and never lose track of what you watch.
            </p>
          </motion.div>

          {/* Quick stats */}
          <div className="flex flex-wrap gap-4 mt-8">
            <StatCard icon={Film} label="Movies" value={stats.movies} color="text-glow" />
            <StatCard icon={Tv} label="Shows" value={stats.shows} color="text-ember" />
            <StatCard icon={Clock} label="Hours" value={stats.hours} color="text-mint" />
            <StatCard icon={Zap} label="Services" value={`${connectedCount}/3`} color="text-rose" />
          </div>
        </div>
      </motion.div>

      {/* Service cards */}
      {connectedCount < 3 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {!wetrakr.connected && <ServicePrompt name="StreamSync" color="glow" path="/settings" />}
          {!trakt.connected && <ServicePrompt name="Trakt" color="flame" path="/settings" />}
          {!tmdbState.connected && <ServicePrompt name="TMDB" color="mint" path="/settings" />}
        </div>
      )}

      {/* Trending */}
      {trending.length > 0 && (
        <section>
          <SectionHeader icon={TrendingUp} title="Trending This Week" />
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {trending.map((item, i) => (
              <PosterCard key={item.id} item={item} index={i} />
            ))}
          </div>
        </section>
      )}

      {/* Popular */}
      {popular.length > 0 && (
        <section>
          <SectionHeader icon={Star} title="Popular Movies" />
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {popular.map((item, i) => (
              <PosterCard key={item.id} item={{ ...item, media_type: 'movie' }} index={i} />
            ))}
          </div>
        </section>
      )}

      {/* Library preview */}
      {library.length > 0 && (
        <section>
          <SectionHeader icon={Film} title="Your Library" link="/library" />
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {library.slice(0, 5).map((item, i) => (
              <PosterCard key={item.id} item={item} index={i} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <motion.div
      className="glass px-5 py-3 flex items-center gap-3 min-w-[140px]"
      whileHover={{ scale: 1.02 }}
    >
      <div className={`${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <div className="font-display font-bold text-xl text-snow">{value}</div>
        <div className="text-xs text-mist">{label}</div>
      </div>
    </motion.div>
  );
}

function SectionHeader({ icon: Icon, title, link }) {
  return (
    <div className="flex items-center justify-between mb-5">
      <div className="flex items-center gap-3">
        <Icon className="w-5 h-5 text-glow" />
        <h2 className="font-display font-bold text-xl text-snow">{title}</h2>
      </div>
      {link && (
        <motion.a
          href={link}
          className="flex items-center gap-1 text-sm text-mist hover:text-glow transition-colors"
          whileHover={{ x: 4 }}
        >
          View all <ArrowRight className="w-4 h-4" />
        </motion.a>
      )}
    </div>
  );
}

function ServicePrompt({ name, color, path }) {
  return (
    <motion.a
      href={path}
      className={`glass p-5 flex items-center gap-4 hover:border-${color}/30 transition-all group`}
      whileHover={{ scale: 1.02, y: -2 }}
    >
      <div className={`w-12 h-12 rounded-xl bg-${color}/20 flex items-center justify-center`}>
        <Zap className={`w-6 h-6 text-${color}`} />
      </div>
      <div>
        <div className="font-display font-semibold text-snow">Connect {name}</div>
        <div className="text-sm text-mist">Sync your watch history</div>
      </div>
      <ArrowRight className="w-5 h-5 text-mist group-hover:text-snow ml-auto transition-colors" />
    </motion.a>
  );
}
