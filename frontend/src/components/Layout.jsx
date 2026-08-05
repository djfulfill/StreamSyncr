import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, Film, Search, RefreshCw, Settings, Tv, Clapperboard } from 'lucide-react';
import useStore from '../store';

const navItems = [
  { path: '/', icon: Home, label: 'Dashboard' },
  { path: '/library', icon: Film, label: 'Library' },
  { path: '/search', icon: Search, label: 'Search' },
  { path: '/sync', icon: RefreshCw, label: 'Sync' },
  { path: '/imdb', icon: Tv, label: 'IMDb' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout({ children }) {
  const location = useLocation();
  const { wetrakr, trakt, tmdb, imdb, plex, anilist, simkl, jellyfin, kodi } = useStore();

  const services = [
    { name: 'StreamSyncr', connected: wetrakr.connected, color: 'bg-glow' },
    { name: 'Trakt', connected: trakt.connected, color: 'bg-ember' },
    { name: 'TMDB', connected: tmdb.connected, color: 'bg-flame' },
    { name: 'IMDb', connected: imdb.connected, color: 'bg-mint' },
    { name: 'Plex', connected: plex.connected, color: 'bg-rose' },
    { name: 'AniList', connected: anilist.connected, color: 'bg-ember' },
    { name: 'Simkl', connected: simkl.connected, color: 'bg-flame' },
    { name: 'Jellyfin', connected: jellyfin.connected, color: 'bg-glow' },
    { name: 'Kodi', connected: kodi.connected, color: 'bg-flame' },
  ];

  const connectedCount = services.filter((s) => s.connected).length;

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-20 lg:w-72 glass-strong flex flex-col py-6 px-3 lg:px-5 m-3 rounded-2xl relative z-10">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-10 px-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-glow to-ember flex items-center justify-center">
            <Clapperboard className="w-5 h-5 text-void" />
          </div>
          <span className="hidden lg:block font-display font-bold text-xl tracking-tight"> StreamSyncr </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 flex flex-col gap-1">
          {navItems.map(({ path, icon: Icon, label }) => (
            <NavLink key={path} to={path} className="relative">
              {({ isActive }) => (
                <motion.div
                  className={`flex items-center gap-3 px-3 py-3 rounded-xl transition-colors duration-200 ${
                    isActive ? 'bg-glow/20 text-glow' : 'text-mist hover:text-snow hover:bg-ghost'
                  }`}
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span className="hidden lg:block font-medium text-sm">{label}</span>
                  {isActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-glow rounded-r-full"
                    />
                  )}
                </motion.div>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Service status */}
        <div className="mt-auto px-2">
          <div className="hidden lg:block text-xs text-mist mb-3 font-medium uppercase tracking-wider"> Connected </div>
          <div className="flex lg:flex-col gap-2">
            {services.map((s) => (
              <ServiceDot key={s.name} name={s.name} connected={s.connected} color={s.color} />
            ))}
          </div>
          <div className="hidden lg:block mt-3 text-xs text-mist">
            {connectedCount}/{services.length} services
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto py-6 pr-6 pl-2 relative z-10">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="h-full"
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
}

function ServiceDot({ name, connected, color }) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${connected ? color : 'bg-whisper'} ${connected ? 'pulse' : ''}`} />
      <span className="hidden lg:block text-xs text-mist">{name}</span>
    </div>
  );
}
