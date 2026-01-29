import os
import requests
import io
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from fontTools.ttLib import TTFont

THEME_DIR = "grub-theme"
ICONS_DIR = os.path.join(THEME_DIR, "icons")
FONTS_DIR = os.path.join(THEME_DIR, "fonts")

# Colors
COLOR_BG = (20, 18, 24)
COLOR_PRIMARY = (208, 188, 255)
COLOR_PRIMARY_DARK = (56, 30, 114)
COLOR_SURFACE_DARK = (43, 41, 48)
COLOR_SURFACE_VARIANT = (73, 69, 79)
COLOR_OUTLINE = (147, 143, 153)

def create_background():
    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img, "RGBA")

    # Helper to draw radial gradient
    def draw_gradient(center_x, center_y, color, radius_factor):
        # Create a radial gradient mask
        radius = int(max(width, height) * radius_factor)
        gradient = Image.new("L", (radius * 2, radius * 2), 0)
        g_draw = ImageDraw.Draw(gradient)

        # Simple radial gradient: center white, edge black
        # We can simulate this by drawing concentric circles
        for r in range(radius, 0, -2):
            alpha = int(255 * (1 - (r / radius)))
            g_draw.ellipse((radius - r, radius - r, radius + r, radius + r), fill=alpha)

        # Color layer
        color_layer = Image.new("RGBA", (radius * 2, radius * 2), color)
        color_layer.putalpha(gradient)

        # Paste onto image
        img.paste(color_layer, (int(center_x - radius), int(center_y - radius)), color_layer)

    # radial-gradient(at 10% 10%, #2D2A35 0%, transparent 40%)
    draw_gradient(width * 0.1, height * 0.1, (45, 42, 53), 0.4)
    # radial-gradient(at 90% 10%, #36343B 0%, transparent 40%)
    draw_gradient(width * 0.9, height * 0.1, (54, 52, 59), 0.4)
    # radial-gradient(at 50% 50%, #1C1B1F 0%, transparent 50%)
    draw_gradient(width * 0.5, height * 0.5, (28, 27, 31), 0.5)
    # radial-gradient(at 85% 85%, #3F3C45 0%, transparent 40%)
    draw_gradient(width * 0.85, height * 0.85, (63, 60, 69), 0.4)
    # radial-gradient(at 15% 85%, #2B2930 0%, transparent 40%)
    draw_gradient(width * 0.15, height * 0.85, (43, 41, 48), 0.4)

    img.save(os.path.join(THEME_DIR, "background.png"))
    print("Background generated.")

def create_selection_box():
    # Style: Glass Pill Active
    # bg-[#D0BCFF]/10 -> (208, 188, 255, 25) (approx 10%)
    # border-[#D0BCFF]/50 -> (208, 188, 255, 128)
    # shadow-[0_0_30px_rgba(208,188,255,0.15)]

    # We need to create the center, and the edges/corners for a scalable box.
    # GRUB menu items have variable width/height.
    # We will generate a single large image for the selection to avoid complex slicing if possible,
    # OR generate the 9-slice components. GRUB supports stretching center.

    # Let's make a generic pill shape with corner radius 32.
    # Size: let's make it 100x100 for the corners and center.

    radius = 32
    size = radius * 3 # 96x96

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bg_color = (208, 188, 255, 25)
    border_color = (208, 188, 255, 128)

    # Draw rounded rect
    draw.rounded_rectangle((0, 0, size-1, size-1), radius=radius, fill=bg_color, outline=border_color, width=1)

    # To enable scaling, we slice this.
    # North-West
    img.crop((0, 0, radius, radius)).save(os.path.join(THEME_DIR, "selection_nw.png"))
    # North
    img.crop((radius, 0, size-radius, radius)).save(os.path.join(THEME_DIR, "selection_n.png"))
    # North-East
    img.crop((size-radius, 0, size, radius)).save(os.path.join(THEME_DIR, "selection_ne.png"))
    # West
    img.crop((0, radius, radius, size-radius)).save(os.path.join(THEME_DIR, "selection_w.png"))
    # Center
    img.crop((radius, radius, size-radius, size-radius)).save(os.path.join(THEME_DIR, "selection_c.png"))
    # East
    img.crop((size-radius, radius, size, size-radius)).save(os.path.join(THEME_DIR, "selection_e.png"))
    # South-West
    img.crop((0, size-radius, radius, size)).save(os.path.join(THEME_DIR, "selection_sw.png"))
    # South
    img.crop((radius, size-radius, size-radius, size)).save(os.path.join(THEME_DIR, "selection_s.png"))
    # South-East
    img.crop((size-radius, size-radius, size, size)).save(os.path.join(THEME_DIR, "selection_se.png"))

    print("Selection box generated.")

def create_icons():
    # Size 32x32 or 48x48
    size = 48

    def save_icon(name, draw_func):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw_func(draw, size)
        img.save(os.path.join(ICONS_DIR, f"{name}.png"))

    def draw_terminal(d, s):
        # >_
        # White
        fill = (255, 255, 255, 255)
        d.polygon([(s*0.2, s*0.2), (s*0.5, s*0.5), (s*0.2, s*0.8)], fill=fill) # > (filled triangle looks like arrow)
        # Wait, simple line is better
        d.line([(s*0.2, s*0.2), (s*0.5, s*0.5), (s*0.2, s*0.8)], fill=fill, width=4)
        d.line([(s*0.55, s*0.8), (s*0.8, s*0.8)], fill=fill, width=4)

    def draw_windows(d, s):
        fill = (255, 255, 255, 255)
        m = s * 0.1
        h = s / 2
        d.rectangle((m, m, h-2, h-2), fill=fill)
        d.rectangle((h+2, m, s-m, h-2), fill=fill)
        d.rectangle((m, h+2, h-2, s-m), fill=fill)
        d.rectangle((h+2, h+2, s-m, s-m), fill=fill)

    def draw_uefi(d, s):
        fill = (255, 255, 255, 255)
        # Gear
        d.ellipse((s*0.2, s*0.2, s*0.8, s*0.8), outline=fill, width=4)
        d.ellipse((s*0.4, s*0.4, s*0.6, s*0.6), fill=fill)
        # Teeth
        for i in range(0, 360, 45):
            # Simplification: just a ring
            pass
        d.ellipse((s*0.1, s*0.1, s*0.9, s*0.9), outline=fill, width=2)

    def draw_shutdown(d, s):
        fill = (255, 255, 255, 255)
        # Circle with break at top
        d.arc((s*0.1, s*0.1, s*0.9, s*0.9), start=-60, end=240, fill=fill, width=4)
        # Line at top
        d.line((s*0.5, s*0.1, s*0.5, s*0.5), fill=fill, width=4)

    save_icon("type_linux", draw_terminal)
    save_icon("type_windows", draw_windows)
    save_icon("type_uefi", draw_uefi)
    save_icon("type_shutdown", draw_shutdown)
    # Generic
    save_icon("os_linux", draw_terminal)
    save_icon("os_windows", draw_windows)

    print("Icons generated.")

def download_fonts():
    # User agent for legacy format (TTF)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0"
    }

    fonts = [
        ("Inter", "https://fonts.googleapis.com/css2?family=Inter:wght@400;700"),
        ("JetBrainsMono", "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400")
    ]

    for name, url in fonts:
        print(f"Fetching CSS for {name}...")
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            css = r.text
            # Extract first url(...)
            import re
            match = re.search(r'src: url\((.*?)\)', css)
            if match:
                font_url = match.group(1)
                print(f"Downloading font from {font_url}...")
                fr = requests.get(font_url)
                fr.raise_for_status()
                # Determine extension
                ext = "ttf" # Assumed from user agent
                if "woff2" in font_url: ext = "woff2"
                elif "woff" in font_url: ext = "woff"

                filepath = os.path.join(FONTS_DIR, f"{name}.{ext}")
                with open(filepath, "wb") as f:
                    f.write(fr.content)
                print(f"Saved {filepath}")

                if ext == "woff2":
                    try:
                        print("Converting WOFF2 to TTF...")
                        font = TTFont(filepath)
                        new_path = os.path.join(FONTS_DIR, f"{name}.ttf")
                        font.save(new_path)
                        print(f"Converted to {new_path}")
                        os.remove(filepath)
                    except Exception as e:
                        print(f"Conversion failed: {e}")

            else:
                print(f"Could not find font URL for {name}")
        except Exception as e:
            print(f"Error downloading {name}: {e}")

if __name__ == "__main__":
    create_background()
    create_selection_box()
    create_icons()
    download_fonts()
