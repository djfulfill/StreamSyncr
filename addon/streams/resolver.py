from typing import List, Dict
from .providers.realdebrid import RealDebridClient
from .providers.torbox import TorBoxClient
from .providers.alldebrid import AllDebridClient


async def resolve_streams(media_type: str, item_id: str, user_config: dict) -> List[Dict]:
    streams = []
    priority = user_config.get("debrid_priority", ["realdebrid", "torbox", "alldebrid"])

    for service in priority:
        try:
            if service == "realdebrid" and user_config.get("realdebrid_key"):
                client = RealDebridClient(user_config["realdebrid_key"])
                results = client.resolve_imdb(item_id)
                streams.extend(results)

            elif service == "torbox" and user_config.get("torbox_key"):
                client = TorBoxClient(user_config["torbox_key"])
                results = client.resolve_imdb(item_id)
                streams.extend(results)

            elif service == "alldebrid" and user_config.get("alldebrid_key"):
                client = AllDebridClient(user_config["alldebrid_key"])
                results = client.resolve_imdb(item_id)
                streams.extend(results)
        except Exception as e:
            print(f"Error resolving from {service}: {e}")
            continue

    return streams
