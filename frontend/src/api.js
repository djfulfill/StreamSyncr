const TMDB_IMG = 'https://image.tmdb.org/t/p';

export const tmdbImage = (path, size = 'w500') => {
  if (!path) return null;
  return `${TMDB_IMG}/${size}${path}`;
};

export const tmdbBackdrop = (path, size = 'w1280') => {
  if (!path) return null;
  return `${TMDB_IMG}/${size}${path}`;
};

// WeTrakr API
export const wetrakr = {
  async search(query, tokens) {
    const res = await fetch('/api/wetrakr/api/v2/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'wetrakr-api-country': 'US',
        'wetrakr-api-language': 'en-US',
        Cookie: `wta_at=${tokens.accessToken}; wta_rt=${tokens.refreshToken}`,
      },
      body: JSON.stringify({ query, page: 1 }),
    });
    return res.json();
  },

  async getWatched(tokens) {
    const res = await fetch('/api/wetrakr/api/v2/account/tracking', {
      headers: {
        'wetrakr-api-country': 'US',
        'wetrakr-api-language': 'en-US',
        Cookie: `wta_at=${tokens.accessToken}; wta_rt=${tokens.refreshToken}`,
      },
    });
    return res.json();
  },

  async getProfile(tokens) {
    const res = await fetch('/api/wetrakr/api/v2/account/user', {
      headers: {
        'wetrakr-api-country': 'US',
        'wetrakr-api-language': 'en-US',
        Cookie: `wta_at=${tokens.accessToken}; wta_rt=${tokens.refreshToken}`,
      },
    });
    return res.json();
  },

  async markWatched(id, type, tokens) {
    const res = await fetch('/api/wetrakr/api/v2/account/tracking', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'wetrakr-api-country': 'US',
        'wetrakr-api-language': 'en-US',
        Cookie: `wta_at=${tokens.accessToken}; wta_rt=${tokens.refreshToken}`,
      },
      body: JSON.stringify({
        tracking_type: 1,
        id,
        type,
        app: 'web',
      }),
    });
    return res.json();
  },

  async unwatch(tmdbId, type, tokens) {
    const res = await fetch('/api/wetrakr/api/v2/account/tracking/remove', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'wetrakr-api-country': 'US',
        'wetrakr-api-language': 'en-US',
        Cookie: `wta_at=${tokens.accessToken}; wta_rt=${tokens.refreshToken}`,
      },
      body: JSON.stringify({ id: tmdbId, type }),
    });
    return res.json();
  },

  async getFavorites(tokens) {
    const res = await fetch('/api/wetrakr/api/v2/account/favorites', {
      headers: {
        'wetrakr-api-country': 'US',
        'wetrakr-api-language': 'en-US',
        Cookie: `wta_at=${tokens.accessToken}; wta_rt=${tokens.refreshToken}`,
      },
    });
    return res.json();
  },

  async favorite(id, type, tokens) {
    const res = await fetch('/api/wetrakr/api/v2/account/favorites', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'wetrakr-api-country': 'US',
        'wetrakr-api-language': 'en-US',
        Cookie: `wta_at=${tokens.accessToken}; wta_rt=${tokens.refreshToken}`,
      },
      body: JSON.stringify({ id, type }),
    });
    return res.json();
  },

  async getLists(tokens) {
    const res = await fetch('/api/wetrakr/api/v2/account/lists', {
      headers: {
        'wetrakr-api-country': 'US',
        'wetrakr-api-language': 'en-US',
        Cookie: `wta_at=${tokens.accessToken}; wta_rt=${tokens.refreshToken}`,
      },
    });
    return res.json();
  },
};

// Trakt API
export const trakt = {
  async me(token, apiKey) {
    const res = await fetch('/api/trakt/users/me', {
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
    });
    return res.json();
  },

  async collection(token, apiKey) {
    const res = await fetch('/api/trakt/sync/collection', {
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
    });
    return res.json();
  },

  async history(token, apiKey) {
    const res = await fetch('/api/trakt/sync/history', {
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
    });
    return res.json();
  },

  async watchlist(token, apiKey) {
    const res = await fetch('/api/trakt/sync/watchlist', {
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
    });
    return res.json();
  },

  async ratings(token, apiKey) {
    const res = await fetch('/api/trakt/sync/ratings', {
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
    });
    return res.json();
  },

  async favorites(token, apiKey) {
    const res = await fetch('/api/trakt/sync/favorites', {
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
    });
    return res.json();
  },

  async search(query, token, apiKey) {
    const res = await fetch(`/api/trakt/search/movie,show?query=${encodeURIComponent(query)}`, {
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
    });
    return res.json();
  },

  async trending(token, apiKey) {
    const res = await fetch('/api/trakt/movies/trending', {
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
    });
    return res.json();
  },

  async markWatched(ids, token, apiKey) {
    const res = await fetch('/api/trakt/scrobble/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
      body: JSON.stringify({
        movie: ids,
        progress: 100,
        watched_at: new Date().toISOString(),
      }),
    });
    return res.json();
  },

  async lists(token, apiKey) {
    const res = await fetch('/api/trakt/users/me/lists', {
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
    });
    return res.json();
  },

  async listItems(listId, token, apiKey) {
    const res = await fetch(`/api/trakt/users/me/lists/${listId}/items`, {
      headers: {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        Authorization: `Bearer ${token}`,
        'trakt-api-key': apiKey,
      },
    });
    return res.json();
  },
};

// TMDB API
export const tmdb = {
  async search(query, apiKey) {
    const res = await fetch(`/api/tmdb/3/search/multi?query=${encodeURIComponent(query)}&api_key=${apiKey}`);
    return res.json();
  },

  async movie(id, apiKey) {
    const res = await fetch(`/api/tmdb/3/movie/${id}?api_key=${apiKey}`);
    return res.json();
  },

  async tv(id, apiKey) {
    const res = await fetch(`/api/tmdb/3/tv/${id}?api_key=${apiKey}`);
    return res.json();
  },

  async trending(apiKey) {
    const res = await fetch(`/api/tmdb/3/trending/all/week?api_key=${apiKey}`);
    return res.json();
  },

  async popular(apiKey) {
    const res = await fetch(`/api/tmdb/3/movie/popular?api_key=${apiKey}`);
    return res.json();
  },

  async topRated(apiKey) {
    const res = await fetch(`/api/tmdb/3/movie/top_rated?api_key=${apiKey}`);
    return res.json();
  },

  async nowPlaying(apiKey) {
    const res = await fetch(`/api/tmdb/3/movie/now_playing?api_key=${apiKey}`);
    return res.json();
  },

  async movieCredits(id, apiKey) {
    const res = await fetch(`/api/tmdb/3/movie/${id}/credits?api_key=${apiKey}`);
    return res.json();
  },

  async tvCredits(id, apiKey) {
    const res = await fetch(`/api/tmdb/3/tv/${id}/credits?api_key=${apiKey}`);
    return res.json();
  },

  async movieWatchProviders(id, apiKey) {
    const res = await fetch(`/api/tmdb/3/movie/${id}/watch/providers?api_key=${apiKey}`);
    return res.json();
  },

  async genres(apiKey) {
    const res = await fetch(`/api/tmdb/3/genre/movie/list?api_key=${apiKey}`);
    return res.json();
  },
};

// Plex API (via Python backend)
export const plex = {
  async getLibraries(config) {
    const res = await fetch('/api/plex/libraries', {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },
  async getHistory(config, libraryId) {
    const res = await fetch('/api/plex/history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...config, libraryId }),
    });
    return res.json();
  },
  async search(config, query) {
    const res = await fetch('/api/plex/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...config, query }),
    });
    return res.json();
  },
};

// AniList API
export const anilist = {
  async search(query, accessToken) {
    const res = await fetch('/api/anilist/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, accessToken }),
    });
    return res.json();
  },
  async trending() {
    const res = await fetch('/api/anilist/trending');
    return res.json();
  },
  async getLists(username, accessToken) {
    const res = await fetch('/api/anilist/lists', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, accessToken }),
    });
    return res.json();
  },
};

// Simkl API
export const simkl = {
  async search(query, config) {
    const res = await fetch('/api/simkl/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, ...config }),
    });
    return res.json();
  },
  async trending(config) {
    const res = await fetch('/api/simkl/trending', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },
  async history(config) {
    const res = await fetch('/api/simkl/history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },
};

// Kodi API
export const kodi = {
  async ping(config) {
    const res = await fetch('/api/kodi/ping', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },
  async getMovies(config) {
    const res = await fetch('/api/kodi/movies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },
  async getShows(config) {
    const res = await fetch('/api/kodi/shows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },
  async getEpisodes(config) {
    const res = await fetch('/api/kodi/episodes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },
  async search(config, query) {
    const res = await fetch('/api/kodi/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...config, query }),
    });
    return res.json();
  },
  async getStats(config) {
    const res = await fetch('/api/kodi/stats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },
};

// Jellyfin API
export const jellyfin = {
  async getLibraries(config) {
    const res = await fetch('/api/jellyfin/libraries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },
  async getHistory(config) {
    const res = await fetch('/api/jellyfin/history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },
  async search(config, query) {
    const res = await fetch('/api/jellyfin/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...config, query }),
    });
    return res.json();
  },
};

// IMDb API
export const imdb = {
  async graphql(query, variables = {}) {
    const res = await fetch('/api/imdb/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, variables }),
    });
    return res.json();
  },

  async getLists() {
    const query = `query YourListsSidebar { currentUser { lists { edges { node { id name { originalText text } items { total } } } } } }`;
    return this.graphql(query);
  },

  async getRatings() {
    const query = `query PersonalizedUserData { currentUser { ratings { edges { node { id titleText year releaseDate { year month day } rating { currentRating } } } } } }`;
    return this.graphql(query);
  },

  async getRecentlyViewed() {
    const query = `query RVI_Items { recentlyViewedItems { items { id titleText releaseYear { year } rating { aggregateRating } } } }`;
    return this.graphql(query);
  },

  async createList(name, description = '') {
    const query = `mutation CreateList($input: CreateListInput!) { createList(input: $input) { list { id name { originalText } } } }`;
    return this.graphql(query, {
      input: { name, description, listType: 'WATCH_LIST', allowDuplicates: false },
    });
  },

  async addToList(listId, itemId) {
    const query = `mutation AddItemToList($input: AddItemToListInput!) { addItemToList(input: $input) { list { id } } }`;
    return this.graphql(query, {
      input: { listId, item: { itemElementId: itemId } },
    });
  },

  async removeFromList(listId, itemId) {
    const query = `mutation RemoveElementFromList($input: RemoveElementFromListInput!) { removeElementFromList(input: $input) { list { id } } }`;
    return this.graphql(query, {
      input: { listId, itemId },
    });
  },

  async rateTitle(itemId, rating) {
    const query = `mutation RateTitle($input: RateTitleInput!) { rateTitle(input: $input) { code } }`;
    return this.graphql(query, {
      input: { itemId, rating },
    });
  },

  async deleteRating(itemId) {
    const query = `mutation DeleteTitleRating($input: DeleteTitleRatingInput!) { deleteTitleRating(input: $input) { code } }`;
    return this.graphql(query, {
      input: { itemId },
    });
  },

  async deleteList(listId) {
    const query = `mutation DeleteList($input: DeleteListInput!) { deleteList(input: $input) { code } }`;
    return this.graphql(query, {
      input: { listId },
    });
  },
};
