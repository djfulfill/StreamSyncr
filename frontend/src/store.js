import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useStore = create(
  persist(
    (set, get) => ({
      // Auth state
      wetrakr: { connected: false, username: null, accessToken: null, refreshToken: null, health: null, lastChecked: null },
      trakt: { connected: false, username: null, token: null, apiKey: null, health: null, lastChecked: null },
      tmdb: { connected: false, username: null, apiKey: null, health: null, lastChecked: null },
      imdb: { connected: false, sessionId: null, atMain: null, sessionToken: null, ubidMain: null, sessAtMain: null, health: null, lastChecked: null },
      plex: { connected: false, username: null, token: null, baseUrl: null, health: null, lastChecked: null },
      anilist: { connected: false, username: null, accessToken: null, health: null, lastChecked: null },
      simkl: { connected: false, username: null, accessToken: null, clientId: null, health: null, lastChecked: null },
      jellyfin: { connected: false, username: null, apiKey: null, userId: null, baseUrl: null, health: null, lastChecked: null },
      kodi: { connected: false, username: null, baseUrl: null, health: null, lastChecked: null },
      realdebrid: { connected: false, username: null, apiKey: null, health: null, lastChecked: null, premium: false },
      torbox: { connected: false, username: null, apiKey: null, health: null, lastChecked: null },
      alldebrid: { connected: false, username: null, apiKey: null, health: null, lastChecked: null, premium: false },
      letterboxd: { connected: false, username: null, cookies: null, csrf: null, health: null, lastChecked: null },
      sofasidekick: { connected: false, username: null, sessionId: null, cfClearance: null, cfBm: null, health: null, lastChecked: null },

      // Library state
      library: [],
      watchlist: [],
      favorites: [],
      ratings: {},
      history: [],

      // Extension state
      extension: { detected: false, connected: false, lastSync: null },

      // Scrobble state
      nowPlaying: [],
      _scrobbleWs: null,
      _scrobbleReconnectTimer: null,

      // UI state
      activeTab: 'library',
      searchQuery: '',
      searchResults: [],
      selectedItem: null,
      syncStatus: 'idle',
      isLoading: false,

      // Auth actions
      connectWeTrakr: (username, accessToken, refreshToken) =>
        set({ wetrakr: { connected: true, username, accessToken, refreshToken, health: null, lastChecked: null } }),

      connectTrakt: (username, token, apiKey) =>
        set({ trakt: { connected: true, username, token, apiKey, health: null, lastChecked: null } }),

      connectTMDB: (username, apiKey) =>
        set({ tmdb: { connected: true, username, apiKey, health: null, lastChecked: null } }),

      connectIMDb: (sessionId, atMain, sessionToken, ubidMain = null, sessAtMain = null) =>
        set({ imdb: { connected: true, sessionId, atMain, sessionToken, ubidMain, sessAtMain, health: null, lastChecked: null } }),

      connectPlex: (username, token, baseUrl) =>
        set({ plex: { connected: true, username, token, baseUrl, health: null, lastChecked: null } }),

      connectAniList: (username, accessToken) =>
        set({ anilist: { connected: true, username, accessToken, health: null, lastChecked: null } }),

      connectSimkl: (username, accessToken, clientId) =>
        set({ simkl: { connected: true, username, accessToken, clientId, health: null, lastChecked: null } }),

      connectJellyfin: (username, apiKey, userId, baseUrl) =>
        set({ jellyfin: { connected: true, username, apiKey, userId, baseUrl, health: null, lastChecked: null } }),

      connectKodi: (username, baseUrl) =>
        set({ kodi: { connected: true, username, baseUrl, health: null, lastChecked: null } }),

      connectRealDebrid: (username, apiKey, premium = false) =>
        set({ realdebrid: { connected: true, username, apiKey, health: null, lastChecked: null, premium } }),

      connectTorBox: (username, apiKey) =>
        set({ torbox: { connected: true, username, apiKey, health: null, lastChecked: null } }),

      connectAllDebrid: (username, apiKey, premium = false) =>
        set({ alldebrid: { connected: true, username, apiKey, health: null, lastChecked: null, premium } }),

      connectLetterboxd: (username, cookies, csrf) =>
        set({ letterboxd: { connected: true, username, cookies, csrf, health: null, lastChecked: null } }),

      connectSofaSidekick: (username, sessionId, cfClearance, cfBm) =>
        set({ sofasidekick: { connected: true, username, sessionId, cfClearance, cfBm, health: null, lastChecked: null } }),

      disconnectService: (service) =>
        set((state) => ({
          [service]: { connected: false, username: null, token: null, apiKey: null, health: null, lastChecked: null },
        })),

      // Health check actions
      setServiceHealth: (service, health, detail = null) =>
        set((state) => ({
          [service]: { ...state[service], health, lastChecked: Date.now(), healthDetail: detail },
        })),

      checkAllHealth: async () => {
        const state = get();
        const services = ['wetrakr', 'trakt', 'tmdb', 'imdb', 'letterboxd', 'sofasidekick', 'realdebrid', 'torbox', 'alldebrid', 'plex', 'anilist', 'simkl', 'jellyfin', 'kodi'];
        for (const svc of services) {
          if (state[svc]?.connected) {
            // Set checking state
            set((s) => ({ [svc]: { ...s[svc], health: 'checking' } }));
          }
        }
      },

      // Extension actions
      setExtensionDetected: (detected) =>
        set((state) => ({ extension: { ...state.extension, detected } })),

      setExtensionConnected: (connected) =>
        set((state) => ({ extension: { ...state.extension, connected } })),

      connectServiceFromExtension: (serviceId, data) => {
        const actions = {
          imdb: () => set({
            imdb: {
              connected: true,
              sessionId: data.cookies?.['session-id'] || data.sessionId,
              atMain: data.cookies?.['at-main'] || data.atMain,
              sessionToken: data.cookies?.['session-token'] || data.sessionToken,
              ubidMain: data.cookies?.['ubid-main'] || data.ubidMain,
              sessAtMain: data.cookies?.['sess-at-main'] || data.sessAtMain,
            },
          }),
          wetrakr: () => set({
            wetrakr: {
              connected: true,
              accessToken: data.cookies?.['wta_at'] || data.accessToken,
              refreshToken: data.cookies?.['wta_rt'] || data.refreshToken,
              username: data.username || 'extension_user',
            },
          }),
          letterboxd: () => set({
            // Letterboxd doesn't have a dedicated store entry yet
            // Store in extension config for now
          }),
          sofasidekick: () => set({
            // Sofa Sidekick doesn't have a dedicated store entry yet
          }),
        };

        const action = actions[serviceId];
        if (action) action();

        // Update last sync time
        set((state) => ({
          extension: { ...state.extension, lastSync: Date.now() },
        }));
      },

      // Scrobble actions
      connectScrobbleWs: (token) => {
        const wsUrl = `ws://localhost:7800/ws/scrobble?token=${token}`;
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'now_playing') {
            set({ nowPlaying: data.sessions });
          }
        };

        ws.onclose = () => {
          // Reconnect after 3 seconds
          const timer = setTimeout(() => {
            const currentState = get();
            if (currentState.trakt.connected || currentState.plex.connected) {
              get().connectScrobbleWs(token);
            }
          }, 3000);
          set({ _scrobbleReconnectTimer: timer });
        };

        ws.onerror = () => {
          ws.close();
        };

        set({ _scrobbleWs: ws });
      },

      disconnectScrobbleWs: () => {
        const ws = get()._scrobbleWs;
        if (ws) ws.close();
        const timer = get()._scrobbleReconnectTimer;
        if (timer) clearTimeout(timer);
        set({ _scrobbleWs: null, nowPlaying: [], _scrobbleReconnectTimer: null });
      },

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
        realdebrid: state.realdebrid,
        torbox: state.torbox,
        alldebrid: state.alldebrid,
        letterboxd: state.letterboxd,
        sofasidekick: state.sofasidekick,
        extension: state.extension,
        library: state.library,
        watchlist: state.watchlist,
        favorites: state.favorites,
        ratings: state.ratings,
      }),
    }
  )
);

export default useStore;
