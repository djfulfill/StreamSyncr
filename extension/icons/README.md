# StreamSyncr Chrome Extension Icons

To generate the required icons (icon16.png, icon48.png, icon128.png), 
you can use any image editor or convert from the SVG below.

## Quick Generate (using ImageMagick)

```bash
# Install ImageMagick if needed: apt install imagemagick

# Create icons from the SVG
convert -size 16x16 icon.svg icon16.png
convert -size 48x48 icon.svg icon48.png
convert -size 128x128 icon.svg icon128.png
```

## Or use this minimal SVG as icon.svg

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6366f1"/>
      <stop offset="100%" style="stop-color:#8b5cf6"/>
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="24" fill="url(#grad)"/>
  <text x="64" y="80" font-family="Arial" font-size="60" font-weight="bold" fill="white" text-anchor="middle">S</text>
</svg>
```

## Chrome Web Store

For publishing to the Chrome Web Store, you'll also need:
- icon128.png (128x128) - Store listing icon
- icon48.png (48x48) - Extensions page
- icon16.png (16x16) - Favicon/small displays
- screenshot1.png (1280x800) - Store screenshot
