# StreamSyncr Chrome Extension Icons

## Icon Variants

| File | Description | Use Case |
|------|-------------|----------|
| `icon.svg` | **Animated** — rotating sync rings, pulsing play button | Modern browsers, extension popup (if using SVG directly) |
| `icon-static.svg` | **Static** — clean, no animations | PNG generation, Chrome Web Store, fallback |
| `icon16.png` / `icon48.png` / `icon128.png` | Generated from `icon.svg` | Current manifest (animated source) |
| `icon16-static.png` / `icon48-static.png` / `icon128-static.png` | Generated from `icon-static.svg` | Alternative static set |

## Quick Generate (using ImageMagick)

```bash
# Install ImageMagick if needed: apt install imagemagick

# From animated SVG (current)
convert -size 16x16 icon.svg icon16.png
convert -size 48x48 icon.svg icon48.png
convert -size 128x128 icon.svg icon128.png

# From static SVG (cleaner rendering)
convert -size 16x16 icon-static.svg icon16.png
convert -size 48x48 icon-static.svg icon48.png
convert -size 128x128 icon-static.svg icon128.png
```

## Design

- **Background**: Blue → Indigo → Violet gradient (`#0ea5e9` → `#6366f1` → `#8b5cf6`)
- **Play button**: White circle with cyan triangle (streaming)
- **Sync rings**: Cyan → Purple gradient, dashed circles with positioned dots (synchronization)
- **Rounded square**: 28px radius with subtle drop shadow

## Chrome Web Store Requirements

For publishing to the Chrome Web Store, you'll also need:
- `icon128.png` (128×128) — Store listing icon
- `icon48.png` (48×48) — Extensions page
- `icon16.png` (16×16) — Favicon/small displays
- `screenshot1.png` (1280×800) — Store screenshot
- `screenshot2.png` (1280×800) — Additional screenshot
- `promo-tile.png` (440×280) — Promotional tile
- `marquee.png` (1400×560) — Marquee banner

## Current Manifest References

```json
"action": {
  "default_icon": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
},
"icons": {
  "16": "icons/icon16.png",
  "48": "icons/icon48.png",
  "128": "icons/icon128.png"
}
```

Switch to static variants by renaming `icon16-static.png → icon16.png`, etc., or update the manifest paths.