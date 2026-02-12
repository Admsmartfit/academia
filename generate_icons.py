"""Generate PWA icons as simple PNG files using PIL/Pillow.
Run: python generate_icons.py
"""
import os
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed. Generating placeholder SVG icons instead.")
    # Fallback: create simple SVG-based icons
    SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
    ICONS_DIR = os.path.join('app', 'static', 'icons')
    os.makedirs(ICONS_DIR, exist_ok=True)

    for size in SIZES:
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <rect width="{size}" height="{size}" rx="{size//8}" fill="#0F172A"/>
  <circle cx="{size//2}" cy="{size*0.38}" r="{size*0.22}" fill="#FF6B35"/>
  <text x="{size//2}" y="{size*0.42}" text-anchor="middle" fill="white"
        font-family="Arial,sans-serif" font-weight="bold" font-size="{size*0.18}">⚡</text>
  <text x="{size//2}" y="{size*0.72}" text-anchor="middle" fill="#FF6B35"
        font-family="Arial,sans-serif" font-weight="bold" font-size="{size*0.1}">BIO</text>
  <text x="{size//2}" y="{size*0.85}" text-anchor="middle" fill="#94A3B8"
        font-family="Arial,sans-serif" font-size="{size*0.065}">STUDIO</text>
</svg>'''
        filepath = os.path.join(ICONS_DIR, f'icon-{size}x{size}.png')
        # Save as SVG with .png extension as placeholder
        # For production, convert to actual PNG
        with open(filepath.replace('.png', '.svg'), 'w') as f:
            f.write(svg)
        print(f"Created {filepath.replace('.png', '.svg')}")

    print("\nNote: These are SVG placeholders. For production, convert to PNG using:")
    print("  pip install Pillow cairosvg")
    exit(0)

# If Pillow is available, generate proper PNGs
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
ICONS_DIR = os.path.join('app', 'static', 'icons')
os.makedirs(ICONS_DIR, exist_ok=True)

BG_COLOR = (15, 23, 42)       # #0F172A
ACCENT_COLOR = (255, 107, 53)  # #FF6B35
TEXT_COLOR = (255, 255, 255)

for size in SIZES:
    img = Image.new('RGBA', (size, size), BG_COLOR + (255,))
    draw = ImageDraw.Draw(img)

    # Rounded rect background
    margin = size // 10
    draw.rounded_rectangle(
        [0, 0, size - 1, size - 1],
        radius=size // 6,
        fill=BG_COLOR
    )

    # Lightning bolt circle
    cx, cy = size // 2, int(size * 0.38)
    r = int(size * 0.22)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT_COLOR)

    # Bolt symbol (simplified)
    bolt_size = int(size * 0.18)
    try:
        font_large = ImageFont.truetype("arial.ttf", bolt_size)
        font_name = ImageFont.truetype("arial.ttf", int(size * 0.12))
        font_sub = ImageFont.truetype("arial.ttf", int(size * 0.07))
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_name = font_large
        font_sub = font_large

    # Draw "BIO" text
    draw.text((size // 2, int(size * 0.68)), "BIO", fill=ACCENT_COLOR, font=font_name, anchor="mm")
    # Draw "STUDIO" text
    draw.text((size // 2, int(size * 0.82)), "STUDIO", fill=(148, 163, 184), font=font_sub, anchor="mm")

    filepath = os.path.join(ICONS_DIR, f'icon-{size}x{size}.png')
    img.save(filepath, 'PNG')
    print(f"Created {filepath} ({size}x{size})")

print(f"\nGenerated {len(SIZES)} icons in {ICONS_DIR}/")
