/**
 * StreamSyncr Metadata Provider for Nuvio
 * 
 * Enriched metadata from TMDB, AniList, and Simkl.
 * Returns metadata instead of streams — Nuvio uses this for posters, descriptions, etc.
 */

const BASE_URL = "http://localhost:7800";

async function getStreams(id, type, title, year, season, episode) {
  // Metadata provider returns empty streams — Nuvio uses getMeta for metadata
  return [];
}

async function getMeta(id, type) {
  try {
    const mediaType = type === "tv" ? "series" : type;
    
    const url = `${BASE_URL}/api/v1/meta/${mediaType}/${id}?config_token=${getConfigToken()}`;
    
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "Nuvio-StreamSyncr/2.0",
      },
    });
    
    if (!response.ok) return null;
    
    const data = await response.json();
    return {
      id: data.id || id,
      type: type,
      name: data.name || data.title || "",
      year: data.year,
      poster: data.poster,
      background: data.background,
      description: data.description,
      runtime: data.runtime,
      rating: data.imdb_rating,
      genres: data.genres || [],
    };
  } catch (error) {
    console.error("StreamSyncr Metadata error:", error);
    return null;
  }
}

function getConfigToken() {
  return "";
}

if (typeof globalThis !== "undefined") {
  globalThis.getStreams = getStreams;
  globalThis.getMeta = getMeta;
}
