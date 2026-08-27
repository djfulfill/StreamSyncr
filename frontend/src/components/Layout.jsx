import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Home, Film, Search, RefreshCw, Settings, Tv, Clapperboard } from 'lucide-react';
import useStore from '../store';

const navItems = [
  { path: '/', icon: Home, label: 'Dashboard', key: '1' },
  { path: '/library', icon: Film, label: 'Library', key: '2' },
  { path: '/search', icon: Search, label: 'Search', key: '3' },
  { path: '/sync', icon: RefreshCw, label: 'Sync', key: '4' },
  { path: '/imdb', icon: Tv, label: 'IMDb', key: '5' },
  { path: '/settings', icon: Settings, label: 'Settings', key: '6' },
];

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const store = useStore();

  useEffect(() => {
    const handler = (e) => {
      // Only handle number keys when no input is focused
      if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') return;
      const item = navItems.find((n) => n.key === e.key);
      if (item) {
        e.preventDefault();
        navigate(item.path);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [navigate]);

  const services = [
    { name: 'StreamSyncr', connected: store.wetrakr.connected, health: store.wetrakr.health, color: 'bg-glow' },
    { name: 'Trakt', connected: store.trakt.connected, health: store.trakt.health, color: 'bg-ember' },
    { name: 'TMDB', connected: store.tmdb.connected, health: store.tmdb.health, color: 'bg-flame' },
    { name: 'IMDb', connected: store.imdb.connected, health: store.imdb.health, color: 'bg-mint' },
    { name: 'Letterboxd', connected: store.letterboxd.connected, health: store.letterboxd.health, color: 'bg-emerald-400' },
    { name: 'Plex', connected: store.plex.connected, health: store.plex.health, color: 'bg-rose' },
    { name: 'AniList', connected: store.anilist.connected, health: store.anilist.health, color: 'bg-ember' },
    { name: 'Simkl', connected: store.simkl.connected, health: store.simkl.health, color: 'bg-flame' },
    { name: 'Sofa Sidekick', connected: store.sofasidekick.connected, health: store.sofasidekick.health, color: 'bg-orange-400' },
    { name: 'Jellyfin', connected: store.jellyfin.connected, health: store.jellyfin.health, color: 'bg-glow' },
    { name: 'Kodi', connected: store.kodi.connected, health: store.kodi.health, color: 'bg-flame' },
  ];

  const debridServices = [
    { name: 'Real-Debrid', connected: store.realdebrid.connected, health: store.realdebrid.health, premium: store.realdebrid.premium, color: 'bg-yellow-400' },
    { name: 'TorBox', connected: store.torbox.connected, health: store.torbox.health, color: 'bg-cyan-400' },
    { name: 'AllDebrid', connected: store.alldebrid.connected, health: store.alldebrid.health, premium: store.alldebrid.premium, color: 'bg-violet-400' },
  ];

  const connectedCount = [...services, ...debridServices].filter((s) => s.connected).length;

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="w-20 lg:w-72 glass-strong flex flex-col py-6 px-3 lg:px-5 m-3 rounded-2xl relative z-10 flex-shrink-0 overflow-y-auto">
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
          <div className="hidden lg:block text-xs text-mist mb-3 font-medium uppercase tracking-wider"> Services </div>
          <div className="flex lg:flex-col gap-2">
            {services.map((s) => (
              <ServiceDot key={s.name} name={s.name} connected={s.connected} health={s.health} color={s.color} />
            ))}
          </div>
          <div className="hidden lg:block text-xs text-mist mt-3 mb-2 font-medium uppercase tracking-wider"> Debrid </div>
          <div className="flex lg:flex-col gap-2">
            {debridServices.map((s) => (
              <ServiceDot key={s.name} name={s.name} connected={s.connected} health={s.health} color={s.color} premium={s.premium} />
            ))}
          </div>
          <div className="hidden lg:block mt-3 text-xs text-mist">
            {connectedCount}/{services.length + debridServices.length} services
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto py-6 pr-6 pl-2 relative z-10 scroll-smooth">
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

function ServiceDot({ name, connected, health, color, premium }) {
  const getHealthColor = () => {
    if (!connected) return 'bg-whisper';
    if (health === 'healthy') return color;
    if (health === 'degraded') return 'bg-yellow-400';
    if (health === 'error') return 'bg-rose';
    if (health === 'checking') return 'bg-mist';
    return color; // connected but not checked yet
  };

  const getHealthLabel = () => {
    if (!connected) return '';
    if (health === 'degraded') return ' (degraded)';
    if (health === 'error') return ' (error)';
    if (premium === false && (name === 'Real-Debrid' || name === 'AllDebrid')) return ' (free)';
    return '';
  };

  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${getHealthColor()} ${connected && health !== 'error' ? 'pulse' : ''}`} />
      <span className="hidden lg:block text-xs text-mist">
        {name}{getHealthLabel()}
      </span>
    </div>
  );
}
