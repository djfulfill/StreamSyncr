import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { List, Star, Clock, Plus, Trash2, ExternalLink, RefreshCw } from 'lucide-react';
import useStore from '../store';
import { imdb } from '../api';

export default function IMDb() {
  const { imdb: imdbState } = useStore();
  const [activeTab, setActiveTab] = useState('lists');
  const [lists, setLists] = useState([]);
  const [ratings, setRatings] = useState([]);
  const [recentlyViewed, setRecentlyViewed] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadData = async () => {
    if (!imdbState.connected) return;
    
    setIsLoading(true);
    setError(null);
    try {
      if (activeTab === 'lists') {
        const data = await imdb.getLists();
        setLists(data?.data?.currentUser?.lists?.edges?.map(e => e.node) || []);
      } else if (activeTab === 'ratings') {
        const data = await imdb.getRatings();
        setRatings(data?.data?.currentUser?.ratings?.edges?.map(e => e.node) || []);
      } else if (activeTab === 'recent') {
        const data = await imdb.getRecentlyViewed();
        setRecentlyViewed(data?.data?.recentlyViewedItems?.items || []);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab, imdbState.connected]);

  if (!imdbState.connected) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <div className="glass-strong rounded-2xl p-8 max-w-md text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-ember to-[#d4a80a] flex items-center justify-center mx-auto mb-6">
            <List className="w-8 h-8 text-void" />
          </div>
          <h2 className="text-2xl font-display font-bold mb-4">IMDb Not Connected</h2>
          <p className="text-mist mb-6">
            Connect your IMDb account to sync lists, ratings, and recently viewed items.
          </p>
          <a
            href="/settings"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-ember/20 text-ember font-medium hover:bg-ember/30 transition-colors"
          >
            Go to Settings
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold">IMDb</h1>
          <p className="text-mist mt-1">Lists, ratings, and recently viewed</p>
        </div>
        <button
          onClick={loadData}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-ember/20 text-ember hover:bg-ember/30 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {[
          { id: 'lists', label: 'Lists', icon: List },
          { id: 'ratings', label: 'Ratings', icon: Star },
          { id: 'recent', label: 'Recently Viewed', icon: Clock },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-colors ${
              activeTab === id
                ? 'bg-ember/20 text-ember'
                : 'text-mist hover:text-snow hover:bg-ghost'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {error && (
        <div className="glass rounded-xl p-4 text-red-400 text-sm">
          Error: {error}
        </div>
      )}

      {/* Content */}
      <div className="glass-strong rounded-2xl p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-6 h-6 text-ember animate-spin" />
          </div>
        ) : activeTab === 'lists' ? (
          <ListsTab lists={lists} />
        ) : activeTab === 'ratings' ? (
          <RatingsTab ratings={ratings} />
        ) : (
          <RecentlyViewedTab items={recentlyViewed} />
        )}
      </div>
    </div>
  );
}

function ListsTab({ lists }) {
  if (lists.length === 0) {
    return (
      <div className="text-center py-12">
        <List className="w-12 h-12 text-mist mx-auto mb-4" />
        <p className="text-mist">No lists found</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {lists.map((list) => (
        <motion.a
          key={list.id}
          href={`https://www.imdb.com/list/${list.id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between p-4 rounded-xl bg-ghost/50 hover:bg-ghost transition-colors"
          whileHover={{ x: 4 }}
        >
          <div>
            <h3 className="font-medium">{list.name?.originalText || list.name?.text || 'Untitled'}</h3>
            <p className="text-sm text-mist">{list.items?.total || 0} items</p>
          </div>
          <ExternalLink className="w-4 h-4 text-mist" />
        </motion.a>
      ))}
    </div>
  );
}

function RatingsTab({ ratings }) {
  if (ratings.length === 0) {
    return (
      <div className="text-center py-12">
        <Star className="w-12 h-12 text-mist mx-auto mb-4" />
        <p className="text-mist">No ratings found</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {ratings.map((item) => (
        <div
          key={item.id}
          className="flex items-center justify-between p-4 rounded-xl bg-ghost/50"
        >
          <div>
            <h3 className="font-medium">{item.titleText}</h3>
            <p className="text-sm text-mist">{item.year}</p>
          </div>
          <div className="flex items-center gap-1 text-ember">
            <Star className="w-4 h-4 fill-current" />
            <span className="font-medium">{item.rating?.currentRating || '-'}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function RecentlyViewedTab({ items }) {
  if (items.length === 0) {
    return (
      <div className="text-center py-12">
        <Clock className="w-12 h-12 text-mist mx-auto mb-4" />
        <p className="text-mist">No recently viewed items</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div
          key={item.id}
          className="flex items-center justify-between p-4 rounded-xl bg-ghost/50"
        >
          <div>
            <h3 className="font-medium">{item.titleText}</h3>
            <p className="text-sm text-mist">{item.releaseYear?.year || 'Unknown year'}</p>
          </div>
          {item.rating?.aggregateRating && (
            <div className="flex items-center gap-1 text-ember">
              <Star className="w-4 h-4 fill-current" />
              <span className="font-medium">{item.rating.aggregateRating}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
