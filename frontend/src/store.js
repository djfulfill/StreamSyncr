import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useStore = create(
  persist(
    (set, get) => ({
      // Auth state
      wetrakr: { connected: false, username: null, accessToken: null, refreshToken: null },
      trakt: { connected: false, username: null, token: null, apiKey: null },
      tmdb: { connected: false, username: null, apiKey: null },
      imdb: { connected: false, sessionId: null, atMain: null, sessionToken: null, ubidMain: null, sessAtMain: null },
      plex: { connected: false, username: null, token: null, baseUrl: null },
      anilist: { connected: false, username: null, accessToken: null },
      simkl: { connected: false, username: null, accessToken: null, clientId: null },
      jellyfin: { connected: false, username: null, apiKey: null, userId: null, baseUrl: null },
      kodi: { connected: false, username: null, baseUrl: null },

      // Library state
      library: [],
      watchlist: [],
      favorites: [],
      ratings: {},
      history: [],

      // UI state
      activeTab: 'library',
      searchQuery: '',
      searchResults: [],
      selectedItem: null,
      syncStatus: 'idle',
      isLoading: false,

      // Auth actions
      connectWeTrakr: (username, accessToken, refreshToken) =>
        set({ wetrakr: { connected: true, username, accessToken, refreshToken } }),

      connectTrakt: (username, token, apiKey) =>
        set({ trakt: { connected: true, username, token, apiKey } }),

      connectTMDB: (username, apiKey) =>
        set({ tmdb: { connected: true, username, apiKey } }),

      connectIMDb: (sessionId, atMain, sessionToken, ubidMain = null, sessAtMain = null) =>
        set({ imdb: { connected: true, sessionId, atMain, sessionToken, ubidMain, sessAtMain } }),

      connectPlex: (username, token, baseUrl) =>
        set({ plex: { connected: true, username, token, baseUrl } }),

      connectAniList: (username, accessToken) =>
        set({ anilist: { connected: true, username, accessToken } }),

      connectSimkl: (username, accessToken, clientId) =>
        set({ simkl: { connected: true, username, accessToken, clientId } }),

      connectJellyfin: (username, apiKey, userId, baseUrl) =>
        set({ jellyfin: { connected: true, username, apiKey, userId, baseUrl } }),

      connectKodi: (username, baseUrl) =>
        set({ kodi: { connected: true, username, baseUrl } }),

      disconnectService: (service) =>
        set((state) => ({
          [service]: { connected: false, username: null, token: null, apiKey: null },
        })),

      // Library actions
      setLibrary: (library) => set({ library }),
      setWatchlist: (watchlist) => set({ watchlist }),
      setFavorites: (favorites) => set({ favorites }),
      setRatings: (ratings) => set({ ratings }),
      setHistory: (history) => set({ history }),

      addToLibrary: (item) =>
        set((state) => ({
          library: [...state.library.filter((i) => i.id !== item.id), item],
        })),

      removeFromLibrary: (id) =>
        set((state) => ({
          library: state.library.filter((i) => i.id !== id),
        })),

      // UI actions
      setActiveTab: (tab) => set({ activeTab: tab }),
      setSearchQuery: (query) => set({ searchQuery: query }),
      setSearchResults: (results) => set({ searchResults: results }),
      setSelectedItem: (item) => set({ selectedItem: item }),
      setSyncStatus: (status) => set({ syncStatus: status }),
      setIsLoading: (loading) => set({ isLoading: loading }),
    }),
    {
      name: 'streamsyncr-storage',
      partialize: (state) => ({
        wetrakr: state.wetrakr,
        trakt: state.trakt,
        tmdb: state.tmdb,
        imdb: state.imdb,
        plex: state.plex,
        anilist: state.anilist,
        simkl: state.simkl,
        jellyfin: state.jellyfin,
        kodi: state.kodi,
        library: state.library,
        watchlist: state.watchlist,
        favorites: state.favorites,
        ratings: state.ratings,
      }),
    }
  )
);

export default useStore;
