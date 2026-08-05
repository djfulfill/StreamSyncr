import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Star, Calendar, Clock, Eye, Heart, Bookmark, ExternalLink, Loader2 } from 'lucide-react';
import useStore from '../store';
import { tmdb as tmdbApi, tmdbBackdrop, tmdbImage } from '../api';

export default function Detail() {
  const { type, id } = useParams();
  const navigate = useNavigate();
  const { tmdb: tmdbState, library } = useStore();
  const [item, setItem] = useState(null);
  const [credits, setCredits] = useState(null);
  const [providers, setProviders] = useState(null);
  const [loading, setLoading] = useState(true);

  const isInLibrary = library.some((i) => i.id === Number(id));

  useEffect(() => {
    if (!tmdbState.connected || !tmdbState.apiKey) {
      setLoading(false);
      return;
    }
    const fetchDetails = async () => {
      try {
        const [itemData, creditsData] = await Promise.all([
          type === 'tv' ? tmdbApi.tv(id, tmdbState.apiKey) : tmdbApi.movie(id, tmdbState.apiKey),
          type === 'tv' ? tmdbApi.tvCredits(id, tmdbState.apiKey) : tmdbApi.movieCredits(id, tmdbState.apiKey),
        ]);
        setItem(itemData);
        setCredits(creditsData);
        if (type === 'movie') {
          const providerData = await tmdbApi.movieWatchProviders(id, tmdbState.apiKey);
          setProviders(providerData.results?.US);
        }
      } catch (err) {
        console.error('Failed to fetch details:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [id, type, tmdbState]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-glow animate-spin" />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="text-center py-20">
        <p className="text-mist">Item not found. Connect TMDB to view details.</p>
        <button onClick={() => navigate(-1)} className="text-glow mt-4 inline-block">
          Go back
        </button>
      </div>
    );
  }

  const title = item.title || item.name;
  const year = item.release_date?.substring(0, 4) || item.first_air_date?.substring(0, 4);
  const runtime = item.runtime || item.episode_run_time?.[0];
  const directors = credits?.crew?.filter((c) => c.job === 'Director') || [];
  const cast = credits?.cast?.slice(0, 10) || [];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <motion.button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-mist hover:text-snow transition-colors"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <ArrowLeft className="w-5 h-5" />
        <span className="text-sm">Back</span>
      </motion.button>

      {/* Hero backdrop */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative h-[400px] rounded-3xl overflow-hidden"
      >
        {item.backdrop_path ? (
          <img src={tmdbBackdrop(item.backdrop_path)} alt={title} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full bg-deep" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-void via-void/50 to-transparent" />

        {/* Title overlay */}
        <div className="absolute bottom-0 left-0 right-0 p-8">
          <div className="flex items-end gap-6">
            {/* Poster */}
            {item.poster_path && (
              <motion.img
                src={tmdbImage(item.poster_path, 'w342')}
                alt={title}
                className="w-32 h-48 object-cover rounded-xl shadow-2xl"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 }}
              />
            )}
            <div className="flex-1">
              <h1 className="font-display text-4xl font-bold text-snow">{title}</h1>
              <div className="flex items-center gap-3 mt-3 text-sm">
                {item.vote_average > 0 && (
                  <span className="flex items-center gap-1 text-flame font-semibold">
                    <Star className="w-4 h-4 fill-flame" />
                    {item.vote_average.toFixed(1)}
                  </span>
                )}
                {year && (
                  <span className="flex items-center gap-1 text-mist">
                    <Calendar className="w-4 h-4" />
                    {year}
                  </span>
                )}
                {runtime && (
                  <span className="flex items-center gap-1 text-mist">
                    <Clock className="w-4 h-4" />
                    {runtime}m
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex gap-3"
      >
        <ActionButton icon={Eye} label="Mark Watched" active={isInLibrary} />
        <ActionButton icon={Heart} label="Favorite" />
        <ActionButton icon={Bookmark} label="Add to List" />
        <a
          href={`https://www.themoviedb.org/${type}/${id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="glass px-5 py-3 rounded-xl flex items-center gap-2 text-sm text-mist hover:text-snow transition-colors"
        >
          <ExternalLink className="w-4 h-4" />
          TMDB
        </a>
      </motion.div>

      {/* Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="lg:col-span-2 space-y-6"
        >
          {/* Overview */}
          {item.overview && (
            <div className="glass-strong p-6">
              <h3 className="font-display font-semibold text-snow mb-3">Overview</h3>
              <p className="text-mist leading-relaxed">{item.overview}</p>
            </div>
          )}

          {/* Cast */}
          {cast.length > 0 && (
            <div className="glass-strong p-6">
              <h3 className="font-display font-semibold text-snow mb-4">Cast</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {cast.map((person) => (
                  <div key={person.id} className="flex items-center gap-3">
                    {person.profile_path ? (
                      <img
                        src={tmdbImage(person.profile_path, 'w185')}
                        alt={person.name}
                        className="w-10 h-10 rounded-full object-cover bg-deep"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-deep flex items-center justify-center text-xs text-whisper">
                        {person.name[0]}
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="text-sm text-snow truncate">{person.name}</p>
                      <p className="text-xs text-mist truncate">{person.character}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>

        {/* Sidebar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-4"
        >
          {/* Details */}
          <div className="glass-strong p-5">
            <h3 className="font-display font-semibold text-snow mb-3">Details</h3>
            <dl className="space-y-2 text-sm">
              {directors.length > 0 && (
                <>
                  <dt className="text-mist">Director</dt>
                  <dd className="text-snow">{directors.map((d) => d.name).join(', ')}</dd>
                </>
              )}
              {item.genres && (
                <>
                  <dt className="text-mist">Genres</dt>
                  <dd className="text-snow">{item.genres.map((g) => g.name).join(', ')}</dd>
                </>
              )}
              {item.status && (
                <>
                  <dt className="text-mist">Status</dt>
                  <dd className="text-snow">{item.status}</dd>
                </>
              )}
              {item.number_of_seasons && (
                <>
                  <dt className="text-mist">Seasons</dt>
                  <dd className="text-snow">{item.number_of_seasons}</dd>
                </>
              )}
            </dl>
          </div>

          {/* Watch providers */}
          {providers?.flatrate && (
            <div className="glass-strong p-5">
              <h3 className="font-display font-semibold text-snow mb-3">Stream</h3>
              <div className="flex flex-wrap gap-2">
                {providers.flatrate.map((p) => (
                  <span key={p.provider_id} className="bg-elevated text-snow text-xs px-3 py-1.5 rounded-lg">
                    {p.provider_name}
                  </span>
                ))}
              </div>
            </div>
          )}
          {providers?.buy && (
            <div className="glass-strong p-5">
              <h3 className="font-display font-semibold text-snow mb-3">Buy</h3>
              <div className="flex flex-wrap gap-2">
                {providers.buy.map((p) => (
                  <span key={p.provider_id} className="bg-elevated text-snow text-xs px-3 py-1.5 rounded-lg">
                    {p.provider_name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

function ActionButton({ icon: Icon, label, active }) {
  return (
    <motion.button
      className={`flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-medium transition-all ${
        active ? 'bg-glow/20 text-glow border border-glow/30' : 'glass text-mist hover:text-snow'
      }`}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <Icon className="w-4 h-4" />
      {label}
    </motion.button>
  );
}
