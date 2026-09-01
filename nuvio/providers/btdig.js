/**
 * StreamSyncr BTDigg Provider for Nuvio
 * 
 * DHT search engine — free, no auth required.
 */

const BASE_URL = "http://localhost:7800";

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
    
    if (!response.ok) return [];
    
    const data = await response.json();
    return (data.streams || []).map((stream) => ({
      name: stream.name || "StreamSyncr",
      title: stream.title || "Unknown",
      url: stream.url,
      behaviorHints: {
        bingeGroup: `streamsyncr-btdig-${id}`,
      },
    }));
  } catch (error) {
    console.error("StreamSyncr BTDigg error:", error);
    return [];
  }
}

function getConfigToken() {
  return "";
}

if (typeof globalThis !== "undefined") {
  globalThis.getStreams = getStreams;
}
