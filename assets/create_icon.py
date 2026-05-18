"""
assets/create_icon.py
Génère assets/logo.ico — logo PlanHub (cercle bleu "PH")
Exécuté par le CI GitHub Actions AVANT pyinstaller.
Requiert Pillow (pip install Pillow).
Compatible Python 3.9+ / Pillow 9+ / Windows CI runner.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_ICO    = os.path.join(SCRIPT_DIR, "logo.ico")

BLUE  = (21, 101, 192, 255)   # #1565C0
WHITE = (255, 255, 255, 255)


def _load_font(size: int) -> ImageFont.ImageFont:
    """
    Charge une police grasse disponible sur Windows/Linux/macOS/CI.
    Priorité : chemins absolus Windows → noms génériques → défaut PIL.
    """
    candidates = [
        # Chemins absolus Windows (GitHub Actions runner)
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\Arial Bold.ttf",
        r"C:\Windows\Fonts\verdanab.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        # Linux (Ubuntu CI)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        # macOS
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        # Noms simples (si dans le PATH des fonts)
        "arialbd.ttf",
        "DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue

    # Fallback ultime : police bitmap intégrée à Pillow
    try:
        # Pillow >= 10.1 accepte size=
        return ImageFont.load_default(size=size)
    except TypeError:
        pass
    return ImageFont.load_default()


def _make_frame(size: int) -> Image.Image:
    """Dessine une frame du logo à la taille demandée."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = max(2, size // 14)

    # Cercle bleu plein
    draw.ellipse([pad, pad, size - pad, size - pad], fill=BLUE)

    # Texte "PH" centré
    font_size = max(8, int(size * 0.38))
    font = _load_font(font_size)
    text = "PH"

    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (size - tw) // 2 - bbox[0]
        ty = (size - th) // 2 - bbox[1]
    except AttributeError:
        # Pillow < 8 : utiliser textsize (déprécié)
        tw, th = draw.textsize(text, font=font)
        tx = (size - tw) // 2
        ty = (size - th) // 2

    # Légère ombre
    draw.text((tx + max(1, size // 40), ty + max(1, size // 40)),
              text, font=font, fill=(0, 0, 0, 80))
    # Texte blanc
    draw.text((tx, ty), text, font=font, fill=WHITE)

    return img


def generate_ico(output_path: str):
    """Génère un ICO multi-résolution (16 à 256 px)."""
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [_make_frame(s) for s in sizes]

    frames[0].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    kb = os.path.getsize(output_path) // 1024
    print(f"OK logo.ico genere : {output_path}  ({len(sizes)} resolutions, {kb} KB)")


if __name__ == "__main__":
    try:
        generate_ico(OUT_ICO)
    except Exception as exc:
        print(f"ERREUR generate_ico: {exc}", file=sys.stderr)
        sys.exit(1)
