#!/usr/bin/env python3
"""
Shrink photos for documentation and copy them into docs/images/.

Setup (once):   pip install Pillow
Usage:          python tools/resize_photos.py PATH [PATH ...] [--width 1600] [--quality 82]

PATH can be a folder or individual image files. Originals are never modified.
Output is JPEG, max 1600px wide, with phone rotation applied and location
(GPS) data stripped.
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is not installed. Run:  pip install Pillow")

try:  # Optional: lets iPhone HEIC photos be read.
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic"}
OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"


def collect(paths):
    for p in map(Path, paths):
        if p.is_dir():
            yield from sorted(f for f in p.rglob("*") if f.suffix.lower() in EXTENSIONS)
        elif p.suffix.lower() in EXTENSIONS:
            yield p
        else:
            print(f"skipped (not an image): {p}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--quality", type=int, default=82)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = after = count = 0

    for src in collect(args.paths):
        try:
            with Image.open(src) as im:
                im = ImageOps.exif_transpose(im)  # apply phone rotation
                if im.mode not in ("RGB", "L"):
                    im = im.convert("RGB")
                if im.width > args.width:
                    h = round(im.height * args.width / im.width)
                    im = im.resize((args.width, h), Image.LANCZOS)
                name = src.stem.lower().replace(" ", "-") + ".jpg"
                dst = OUT_DIR / name
                # Saving without exif drops GPS location and camera metadata.
                im.save(dst, "JPEG", quality=args.quality, optimize=True, progressive=True)
        except Exception as e:
            print(f"failed: {src} ({e})")
            continue
        b, a = src.stat().st_size, dst.stat().st_size
        before += b
        after += a
        count += 1
        print(f"{src.name:40s} {b/1e6:6.1f} MB -> {a/1e3:6.0f} KB   {dst.name}")

    if count:
        print(f"\n{count} photos: {before/1e6:.1f} MB -> {after/1e6:.1f} MB, saved to {OUT_DIR}")
    else:
        print("No images found.")


if __name__ == "__main__":
    main()
