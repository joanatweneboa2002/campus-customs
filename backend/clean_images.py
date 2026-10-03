"""Make every product photo clear, consistent and web-ready.

The raw photos in data/products are messy: many have a transparent background
flattened to solid black (dark navy garments vanish into it), some sit in a white
box inside black bars, some garments are tiny in the frame, several are small and
soft (450-600 px), and their outlines are pixelated stair-steps. For each photo:

  0. Per-photo fixes if needed (crop out a model's chin and jeans, drop his neck).
  1. Paints any pure-black border background white, so the cut-out model sees
     the garment clearly (navy on black is hard to separate).
  2. Enlarges to a 2400 px working size. Small originals (< SMALL_SOURCE px) use Real-ESRGAN (AI upscaler)
     blended with a plain Lanczos enlargement: ESRGAN makes lettering crisp but makes
     heathered fabric look "painted", so the blend keeps real texture. Larger
     originals just use Lanczos (they're already sharp).
  3. Cuts out the garment with rembg (BiRefNet AI background removal).
  4. Smooths the outline: the mask is blurred and re-sharpened at 4x size, which
     rounds off stair-step edges left by the old pixelated backgrounds; pixels along
     the new edge get the garment's own nearby color, so no notches or halo survive.
  5. Crops tight to the garment and centers it on a square canvas with even
     padding, so every product shows at the same size; light sharpen + color lift.

Output: data/products_web/<name>.webp (originals are never modified).

Run:  python backend/clean_images.py            (all photos)
      python backend/clean_images.py name ...   (just some, by file stem)
Needs the Real-ESRGAN binary at ~/.local/lib/realesrgan (or $REALESRGAN_DIR); without it,
small photos fall back to Lanczos only.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter
from rembg import new_session, remove

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SRC_DIR = DATA_DIR / "products"
OUT_DIR = DATA_DIR / "products_web"
OUT_SIZE = 1000   # final square size in px
PADDING = 0.07    # empty margin around the garment, as a fraction of the canvas
BLACK_THRESHOLD = 8  # the flattened background is pure black
WORK_SIZE = 2400  # working resolution (long side) for cut-out + edge smoothing
SMALL_SOURCE = 700  # longest side below this -> AI upscale (blended)
ESRGAN_WEIGHT = 0.65  # share of the Real-ESRGAN image in the blend
EDGE_BLUR = 8  # px at WORK_SIZE: rounds off stair-steps without losing the garment's shape
ESRGAN_DIR = Path(os.environ.get("REALESRGAN_DIR", Path.home() / ".local/lib/realesrgan"))

# Per-photo fixes, as (left, top, right, bottom) crops of the ORIGINAL image.
SOURCE_CROPS = {
    # model photo: drop his chin (rows 0-23) and the jeans below the hem (rows 752+)
    "the-forest-school-hoodie": (0, 24, 800, 752),
}
# Per-photo: whiten skin-colored pixels in the top N rows (after cropping), so the
# cut-out drops a model's neck that shows between the sides of a hood.
REMOVE_SKIN_TOP_ROWS = {"the-forest-school-hoodie": 110}


def remove_skin(img: Image.Image, rows: int) -> Image.Image:
    a = np.asarray(img).astype(int).copy()
    top = a[:rows]
    r, g, b = top[..., 0], top[..., 1], top[..., 2]
    skin = (r > 110) & (r > g + 8) & (g > b) & (r - b > 25)
    top[skin] = 255
    # also clear the soft shadow just under the chin
    a[:rows] = top
    return Image.fromarray(a.astype("uint8"))


def whiten_black_border(img: Image.Image) -> Image.Image:
    """Replace pure-black background connected to the image edge with white."""
    r, g, b = img.split()
    brightest = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mask = brightest.point(lambda v: 255 if v < BLACK_THRESHOLD else 0)
    w, h = mask.size
    edge = [(x, y) for x in range(0, w, 4) for y in (0, h - 1)]
    edge += [(x, y) for y in range(0, h, 4) for x in (0, w - 1)]
    for xy in edge:
        if mask.getpixel(xy) == 255:
            ImageDraw.floodfill(mask, xy, 128)
    background = mask.point(lambda v: 255 if v == 128 else 0)
    # Grow slightly so the dark JPEG fringe around the garment is whitened too.
    background = background.filter(ImageFilter.MaxFilter(5))
    white = Image.new("RGB", img.size, (255, 255, 255))
    return Image.composite(white, img, background)


def realesrgan_x4(img: Image.Image) -> Image.Image | None:
    binary = ESRGAN_DIR / "realesrgan-ncnn-vulkan"
    if not binary.exists():
        return None
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "in.png", Path(tmp) / "out.png"
        img.save(src)
        subprocess.run(
            [str(binary), "-i", str(src), "-o", str(dst), "-n", "realesrgan-x4plus", "-m", str(ESRGAN_DIR / "models")],
            check=True, capture_output=True,
        )
        return Image.open(dst).convert("RGB")


def enlarge(img: Image.Image) -> Image.Image:
    """Enlarge so the long side is WORK_SIZE (more than the 1000 px output needs, so the
    edge smoothing has room to work). Small, soft originals get an AI-upscaled blend."""
    scale = WORK_SIZE / max(img.size)
    size = (round(img.width * scale), round(img.height * scale))
    lanczos = img.resize(size, Image.LANCZOS)
    if max(img.size) >= SMALL_SOURCE:
        return lanczos
    ai = realesrgan_x4(img)
    if ai is None:
        return lanczos
    return Image.blend(lanczos, ai.resize(size, Image.LANCZOS), ESRGAN_WEIGHT)


def _bleed(rgb: np.ndarray, hard: np.ndarray, radius: float) -> np.ndarray:
    """Average garment color near each pixel (background ignored), used to fill notches."""
    weights = Image.fromarray((hard * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(radius))
    w = np.asarray(weights).astype(float) / 255
    out = np.empty_like(rgb, dtype=float)
    for c in range(3):
        premult = Image.fromarray((rgb[..., c] * hard).astype("uint8")).filter(ImageFilter.GaussianBlur(radius))
        out[..., c] = np.asarray(premult).astype(float) / np.maximum(w, 1e-3)
    return np.clip(out, 0, 255)


def smooth_edges(cutout: Image.Image) -> Image.Image:
    """Round off stair-stepped outlines and trim the old-background fringe.

    The stair-steps are in the garment's own pixels, so smoothing only the mask would
    leave light notches. Pixels the new smooth edge adds are filled with the garment's
    own nearby color ("edge bleed"), so the outline reads as one clean curve."""
    hard = (np.asarray(cutout.getchannel("A")) > 128).astype(float)
    alpha = Image.fromarray((hard * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(EDGE_BLUR))
    # re-sharpen into a clean edge with a ~2px soft ramp
    alpha = alpha.point(lambda v: 0 if v < 100 else 255 if v > 156 else round((v - 100) * 255 / 56))
    alpha = alpha.filter(ImageFilter.MinFilter(3))

    rgb = np.asarray(cutout.convert("RGB")).astype(float)
    inner = np.asarray(Image.fromarray((hard * 255).astype("uint8")).filter(ImageFilter.MinFilter(5))) > 128
    bleed = _bleed(rgb, inner.astype(float), EDGE_BLUR / 2)
    # keep real pixels well inside the garment; use bled color along the outline
    rgb = np.where(inner[..., None], rgb, bleed)
    out = Image.fromarray(rgb.astype("uint8")).convert("RGBA")
    out.putalpha(alpha)
    return out


def crop_and_center(cutout: Image.Image) -> Image.Image:
    alpha = cutout.getchannel("A").point(lambda v: 255 if v > 20 else 0)
    box = alpha.getbbox() or (0, 0, *cutout.size)
    garment = cutout.crop(box)

    inner = round(OUT_SIZE * (1 - 2 * PADDING))
    scale = inner / max(garment.size)
    new_size = (max(1, round(garment.width * scale)), max(1, round(garment.height * scale)))
    garment = garment.resize(new_size, Image.LANCZOS)

    canvas = Image.new("RGBA", (OUT_SIZE, OUT_SIZE), (0, 0, 0, 0))
    canvas.paste(garment, ((OUT_SIZE - garment.width) // 2, (OUT_SIZE - garment.height) // 2), garment)
    return canvas


def enhance(img: Image.Image) -> Image.Image:
    alpha = img.getchannel("A")
    rgb = img.convert("RGB")
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.5, percent=70, threshold=2))
    rgb = ImageEnhance.Contrast(rgb).enhance(1.05)
    rgb = ImageEnhance.Color(rgb).enhance(1.06)
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def process(src: Path, session, out_dir: Path) -> None:
    img = Image.open(src).convert("RGB")
    if src.stem in SOURCE_CROPS:
        img = img.crop(SOURCE_CROPS[src.stem])
    if src.stem in REMOVE_SKIN_TOP_ROWS:
        img = remove_skin(img, REMOVE_SKIN_TOP_ROWS[src.stem])
    big = enlarge(whiten_black_border(img))
    cutout = smooth_edges(remove(big, session=session))
    final = enhance(crop_and_center(cutout))
    final.save(out_dir / f"{src.stem}.webp", quality=92, method=6)


def main() -> None:
    stems = set(sys.argv[1:])
    sources = [p for p in sorted(SRC_DIR.glob("*.jpg")) if not stems or p.stem in stems]

    # Build into a staging folder and swap at the end, so the live site never
    # shows a half-processed set (it would fall back to the raw photos).
    # A full run resumes: photos already in staging are skipped.
    staging = DATA_DIR / "products_web_staging"
    staging.mkdir(exist_ok=True)
    if stems and OUT_DIR.exists():
        shutil.copytree(OUT_DIR, staging, dirs_exist_ok=True)
    todo = [s for s in sources if stems or not (staging / f"{s.stem}.webp").exists()]

    # One model at a time: BiRefNet needs ~4 GB RAM, so parallel workers thrash a 16 GB Mac.
    session = new_session("birefnet-general-lite")
    for i, src in enumerate(todo, 1):
        process(src, session, staging)
        print(f"[{i}/{len(todo)}] {src.stem}", flush=True)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    staging.rename(OUT_DIR)
    print(f"Done -> {OUT_DIR}")


if __name__ == "__main__":
    main()
