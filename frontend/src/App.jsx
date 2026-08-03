import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Library from './pages/Library';
import Search from './pages/Search';
import Sync from './pages/Sync';
import Settings from './pages/Settings';
import Detail from './pages/Detail';
import IMDb from './pages/IMDb';

export default function App() {
  return (
    <BrowserRouter>
      <div className="grain">
        {/* Ambient glows */}
        <div className="ambient bg-glow top-[-200px] left-[-200px]" />
        <div className="ambient bg-ember bottom-[-200px] right-[-200px]" />

        <Layout>
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/library" element={<Library />} />
              <Route path="/search" element={<Search />} />
              <Route path="/sync" element={<Sync />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/imdb" element={<IMDb />} />
              <Route path="/detail/:type/:id" element={<Detail />} />
            </Routes>
          </AnimatePresence>
        </Layout>
      </div>
    </BrowserRouter>
  );
}
