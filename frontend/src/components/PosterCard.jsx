import { motion } from 'framer-motion';
import { Star, Eye, Heart, Bookmark, Tv, Film } from 'lucide-react';
import { tmdbImage } from '../api';
import { useNavigate } from 'react-router-dom';

export default function PosterCard({ item, index = 0, showMeta = true, focused = false }) {
  const navigate = useNavigate();
  const title = item.title || item.name;
  const year = item.release_date?.substring(0, 4) || item.first_air_date?.substring(0, 4);
  const type = item.media_type || (item.first_air_date ? 'tv' : 'movie');

  return (
    <motion.div
      className={`poster-card cursor-pointer group ${focused ? 'ring-2 ring-glow ring-offset-2 ring-offset-void' : ''}`}
      data-keyboard-card
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      onClick={() => navigate(`/detail/${type}/${item.id}`)}
    >
      {/* Poster image */}
      <div className="aspect-[2/3] bg-deep relative">
        {item.poster_path ? (
          <img src={tmdbImage(item.poster_path)} alt={title} className="w-full h-full object-cover" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-4xl">
              {type === 'tv' ? (
                <Tv className="w-12 h-12 text-whisper" />
              ) : (
                <Film className="w-12 h-12 text-whisper" />
              )}
            </span>
          </div>
        )}

        {/* Hover overlay with info */}
        <div className="absolute inset-0 bg-gradient-to-t from-void/95 via-void/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 flex flex-col justify-end p-4">
          {showMeta && (
            <div className="space-y-2 transform translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
              <div className="flex items-center gap-2">
                {item.vote_average > 0 && (
                  <span className="flex items-center gap-1 text-xs font-semibold text-flame">
                    <Star className="w-3 h-3 fill-flame" />
                    {item.vote_average.toFixed(1)}
                  </span>
                )}
                <span className="text-xs text-mist">{year}</span>
                <span className="text-[10px] uppercase tracking-wider text-mist bg-elevated/60 px-2 py-0.5 rounded-full">
                  {type}
                </span>
              </div>

              {/* Action buttons */}
              <div className="flex gap-2">
                <ActionButton icon={Eye} label="Watched" />
                <ActionButton icon={Heart} label="Favorite" />
                <ActionButton icon={Bookmark} label="List" />
              </div>
            </div>
          )}
        </div>

        {/* Rating badge */}
        {item.vote_average > 0 && (
          <div className="absolute top-2 right-2 bg-void/80 backdrop-blur-sm rounded-lg px-2 py-1 flex items-center gap-1">
            <Star className="w-3 h-3 text-flame fill-flame" />
            <span className="text-xs font-bold text-flame">{item.vote_average.toFixed(1)}</span>
          </div>
        )}
      </div>

      {/* Title */}
      <div className="p-3">
        <h3 className="font-display font-semibold text-sm text-snow truncate">{title}</h3>
        {year && <p className="text-xs text-mist mt-0.5">{year}</p>}
      </div>
    </motion.div>
  );
}

function ActionButton({ icon: Icon, label }) {
  return (
    <motion.button
      className="flex items-center gap-1.5 bg-elevated/80 hover:bg-glow/30 text-snow/80 hover:text-glow text-xs px-2.5 py-1.5 rounded-lg transition-colors"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={(e) => {
        e.stopPropagation();
      }}
    >
      <Icon className="w-3 h-3" />
      <span className="hidden sm:inline">{label}</span>
    </motion.button>
  );
}
