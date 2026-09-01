/**
 * StreamSyncr Torrentio Provider for Nuvio
 * 
 * Searches torrents via StreamSyncr's Torrentio scraper.
 * Runs in Nuvio's QuickJS sandbox — no Node.js APIs available.
 * 
 * Usage: Nuvio calls this provider's getStreams() function
 * with the title's identifiers.
 */

const BASE_URL = "http://localhost:7800"; // StreamSyncr backend

async function getStreams(id, type, title, year, season, episode) {
  try {
    const mediaType = type === "tv" ? "series" : type;
    const imdbId = id || "";
    
    const url = `${BASE_URL}/api/v1/streams/${mediaType}/${imdbId}?config_token=${getConfigToken()}`;
    
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "Nuvio-StreamSyncr/2.0",
      },
    });
    
    if (!response.ok) {
      return [];
    }
    
    const data = await response.json();
    const streams = data.streams || [];
    
    return streams.map((stream) => ({
      name: stream.name || "StreamSyncr",
      title: stream.title || "Unknown",
      url: stream.url,
      behaviorHints: {
        bingeGroup: `streamsyncr-${imdbId}`,
      },
    }));
  } catch (error) {
    console.error("StreamSyncr Torrentio error:", error);
    return [];
  }
}

function getConfigToken() {
  // In Nuvio's QuickJS runtime, config is passed via the provider settings
  // This is a placeholder — in production, the user configures this
  return "";
}

// Nuvio provider entry point
if (typeof globalThis !== "undefined") {
  globalThis.getStreams = getStreams;
}
