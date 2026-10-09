#!/usr/bin/env python3
"""Resize and compress every image in a folder for the web.

For each image in INPUT_DIR this script:
  - scales it down to --max-width pixels wide (keeps aspect ratio; never upscales),
  - sets the DPI metadata to --dpi,
  - saves JPEG at --quality, and optimized PNG/other formats,
and writes the results to OUTPUT_DIR (created if missing).

Usage:
    python image_optimizer.py ./originals ./optimized
    python image_optimizer.py ./originals ./optimized --max-width 800 --quality 80
"""

import argparse
import os
import sys

from PIL import Image

SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")


def optimize_image(src_path, dst_path, max_width=500, dpi=72, quality=85):
    """Optimize a single image. Returns True on success, False on error."""
    try:
        with Image.open(src_path) as img:
            print(f"Processing: {os.path.basename(src_path)}")

            width, height = img.size
            if width > max_width:
                new_width = max_width
                new_height = int(height * (max_width / width))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"  Resized to {new_width}x{new_height}")
            else:
                print(f"  Width {width}px is within the limit, not resized.")

            ext = os.path.splitext(src_path)[1].lower()

            if ext in (".jpg", ".jpeg"):
                # JPEG has no transparency, so flatten RGBA/palette images first
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                img.save(dst_path, "JPEG", dpi=(dpi, dpi), quality=quality, optimize=True)
            elif ext == ".png":
                img.save(dst_path, "PNG", dpi=(dpi, dpi), optimize=True)
            else:
                img.save(dst_path, dpi=(dpi, dpi), optimize=True)

            print(f"  Saved to {dst_path}")
            return True

    except Exception as e:
        print(f"ERROR processing {src_path}: {e}")
        return False


def process_folder(input_dir, output_dir, max_width=500, dpi=72, quality=85):
    """Optimize every supported image in input_dir and write results to output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    processed = 0
    for name in sorted(os.listdir(input_dir)):
        src = os.path.join(input_dir, name)
        dst = os.path.join(output_dir, name)

        if not os.path.isfile(src):
            continue

        if name.lower().endswith(SUPPORTED_EXTENSIONS):
            if optimize_image(src, dst, max_width, dpi, quality):
                processed += 1
        else:
            print(f"Skipping unsupported file: {name}")

    if processed == 0:
        print("No compatible images found.")
    else:
        print(f"\nDone. Optimized {processed} image(s).")
    return processed


def main(argv=None):
    parser = argparse.ArgumentParser(description="Resize and compress images for the web.")
    parser.add_argument("input_dir", help="folder with the original images")
    parser.add_argument("output_dir", help="folder where optimized images will be saved")
    parser.add_argument("--max-width", type=int, default=500, help="maximum width in pixels (default: 500)")
    parser.add_argument("--dpi", type=int, default=72, help="DPI metadata to set (default: 72)")
    parser.add_argument("--quality", type=int, default=85, help="JPEG quality 1-95 (default: 85)")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.input_dir):
        print(f"ERROR: input folder not found: {args.input_dir}", file=sys.stderr)
        return 1
    if os.path.abspath(args.input_dir) == os.path.abspath(args.output_dir):
        print("ERROR: input and output folders must be different.", file=sys.stderr)
        return 1
    if not 1 <= args.quality <= 95:
        print("ERROR: --quality must be between 1 and 95.", file=sys.stderr)
        return 1

    print("Starting image optimization...")
    process_folder(args.input_dir, args.output_dir, args.max_width, args.dpi, args.quality)
    return 0


if __name__ == "__main__":
    sys.exit(main())
