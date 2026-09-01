"""Plugin installer — discovers, installs, and manages external plugins.

External plugins are stored in ~/.streamsyncr/plugins/<name>/ with a
plugin.json manifest. The installer scans this directory and registers
plugins with the PluginRegistry.

plugin.json format:
{
  "name": "my-scraper",
  "version": "1.0.0",
  "type": "scraper",           // "scraper" | "debrid" | "metadata"
  "protocol": "http",          // "http" | "stdio"
  "endpoint": "http://localhost:5580",
  "capabilities": ["torrent-search"],
  "config": {
    "timeout": {"type": "integer", "default": 10}
  }
}
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("streamsyncr.plugins.installer")

PLUGINS_DIR = os.path.expanduser("~/.streamsyncr/plugins")


class PluginInstaller:
    """Discovers and manages external plugins from ~/.streamsyncr/plugins/."""

    def __init__(self, plugins_dir: str = PLUGINS_DIR):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self._installed: dict[str, dict] = {}

    def discover(self) -> list[dict]:
        """Scan plugins directory for plugin.json manifests."""
        manifests = []
        if not self.plugins_dir.exists():
            return manifests

        for entry in self.plugins_dir.iterdir():
            if not entry.is_dir():
                continue
            manifest_path = entry / "plugin.json"
            if not manifest_path.exists():
                continue
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
                manifest["_path"] = str(entry)
                manifests.append(manifest)
                self._installed[manifest["name"]] = manifest
                logger.info(f"Discovered external plugin: {manifest['name']} v{manifest.get('version', '?')}")
            except Exception as e:
                logger.warning(f"Failed to load plugin manifest {manifest_path}: {e}")

        return manifests

    def register_all(self, plugin_registry):
        """Discover and register all external plugins with the plugin registry."""
        manifests = self.discover()
        for manifest in manifests:
            try:
                self._register_one(manifest, plugin_registry)
            except Exception as e:
                logger.warning(f"Failed to register plugin {manifest.get('name')}: {e}")

    def _register_one(self, manifest: dict, plugin_registry):
        """Register a single external plugin."""
        from .external import ExternalScraperPlugin, ExternalDebridPlugin

        name = manifest["name"]
        endpoint = manifest.get("endpoint", "")
        plugin_type = manifest.get("type", "scraper")

        if not endpoint:
            logger.warning(f"Plugin {name} has no endpoint, skipping")
            return

        if plugin_type == "scraper":
            plugin = ExternalScraperPlugin(
                name=name,
                endpoint=endpoint,
                category=manifest.get("category", "external"),
            )
            plugin_registry.register_scraper(plugin)
            logger.info(f"Registered external scraper: {name}")

        elif plugin_type == "debrid":
            plugin = ExternalDebridPlugin(name=name, endpoint=endpoint)
            plugin_registry.register_debrid(name, plugin)
            logger.info(f"Registered external debrid: {name}")

    def install(self, url: str) -> dict:
        """Install a plugin from a URL (downloads plugin.json).

        This is a simplified installer — in production, this would
        download a tarball, verify signatures, etc.
        """
        import urllib.request
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                manifest = json.loads(resp.read())
        except Exception as e:
            return {"error": str(e)}

        name = manifest.get("name")
        if not name:
            return {"error": "No plugin name in manifest"}

        plugin_dir = self.plugins_dir / name
        plugin_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = plugin_dir / "plugin.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        self._installed[name] = manifest
        return {"status": "installed", "name": name, "path": str(plugin_dir)}

    def uninstall(self, name: str) -> dict:
        """Uninstall a plugin by name."""
        plugin_dir = self.plugins_dir / name
        if not plugin_dir.exists():
            return {"error": f"Plugin {name} not found"}
        import shutil
        shutil.rmtree(plugin_dir)
        self._installed.pop(name, None)
        return {"status": "uninstalled", "name": name}

    def list_installed(self) -> list[dict]:
        """List all installed external plugins."""
        self.discover()
        return [
            {
                "name": m["name"],
                "version": m.get("version", "?"),
                "type": m.get("type", "?"),
                "endpoint": m.get("endpoint", ""),
            }
            for m in self._installed.values()
        ]


# ── Global Instance ─────────────────────────────────────────

plugin_installer = PluginInstaller()
