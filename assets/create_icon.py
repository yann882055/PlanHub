"""
assets/create_icon.py
Génère assets/logo.ico — logo PlanHub (cercle bleu "PH")
Exécuté par le CI GitHub Actions AVANT pyinstaller.
Requiert Pillow (pip install Pillow).
"""

import os
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_ICO    = os.path.join(SCRIPT_DIR, "logo.ico")

# ── Palette
BLUE      = (21, 101, 192, 255)   # #1565C0
BLUE_DARK = (13,  71, 161, 255)   # #0D47A1
WHITE     = (255, 255, 255, 255)
SHADOW    = (0,   0,   0,  40)


def _make_frame(size: int) -> Image.Image:
    """Dessine le logo PlanHub à la taille donnée (carré)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = max(2, size // 16)
    r   = size - 2 * pad

    # ── Ombre portée (légère, décalée de 2px)
    shadow_offset = max(1, size // 32)
    draw.ellipse(
        [pad + shadow_offset, pad + shadow_offset,
         pad + r + shadow_offset, pad + r + shadow_offset],
        fill=SHADOW,
    )

    # ── Dégradé simulé : deux cercles concentriques
    draw.ellipse([pad, pad, pad + r, pad + r], fill=BLUE)
    inner = int(r * 0.85)
    inner_pad = pad + (r - inner) // 2
    draw.ellipse(
        [inner_pad, inner_pad,
         inner_pad + inner, inner_pad + inner],
        fill=BLUE,
    )

    # ── Texte "PH"
    font_size = max(6, int(size * 0.38))
    font = None
    for font_name in [
        "arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf",
        "FreeSansBold.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_name, font_size)
            break
        except (IOError, OSError):
            continue
    if font is None:
        try:
            font = ImageFont.load_default(size=font_size)
        except TypeError:
            font = ImageFont.load_default()

    text = "PH"
    # Calculer la bounding box du texte
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1]

    # Ombre légère sur le texte
    draw.text((tx + 1, ty + 1), text, font=font, fill=(0, 0, 0, 80))
    draw.text((tx, ty), text, font=font, fill=WHITE)

    return img


def generate_ico(output_path: str):
    """Génère un ICO multi-résolution."""
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [_make_frame(s) for s in sizes]

    # Pillow écrit un ICO multi-taille avec sizes=
    frames[0].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"✅ Icône générée : {output_path}  ({len(sizes)} résolutions)")


if __name__ == "__main__":
    generate_ico(OUT_ICO)
