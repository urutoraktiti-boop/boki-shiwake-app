#!/usr/bin/env python3
"""Crop one reviewed explanation figure from a rendered PDF page."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def crop_box(value: str) -> tuple[int, int, int, int]:
    try:
        values = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("box must contain four integers") from exc
    if len(values) != 4:
        raise argparse.ArgumentTypeError("box must be LEFT,TOP,RIGHT,BOTTOM")
    left, top, right, bottom = values
    if min(values) < 0 or right <= left or bottom <= top:
        raise argparse.ArgumentTypeError("box coordinates must form a positive rectangle")
    return left, top, right, bottom


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page_image", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--box", required=True, type=crop_box, metavar="L,T,R,B")
    parser.add_argument("--padding", type=int, default=0)
    parser.add_argument("--source-page", required=True, type=int)
    parser.add_argument("--render-dpi", required=True, type=int)
    parser.add_argument("--src", required=True)
    parser.add_argument("--alt", required=True)
    parser.add_argument("--caption", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.padding < 0:
        raise SystemExit("padding must be zero or greater")
    if args.source_page <= 0:
        raise SystemExit("source-page must be positive")
    if not 170 <= args.render_dpi <= 220:
        raise SystemExit("render-dpi must be between 170 and 220")
    if not args.page_image.is_file():
        raise SystemExit(f"page image not found: {args.page_image}")
    if args.output.suffix.lower() != ".png":
        raise SystemExit("output must use the .png extension")

    with Image.open(args.page_image) as source:
        source.load()
        width, height = source.size
        left, top, right, bottom = args.box
        applied = (
            max(0, left - args.padding),
            max(0, top - args.padding),
            min(width, right + args.padding),
            min(height, bottom + args.padding),
        )
        if applied[2] <= applied[0] or applied[3] <= applied[1]:
            raise SystemExit("crop box is outside the source image")
        if right > width or bottom > height:
            raise SystemExit(f"crop box exceeds source dimensions {width}x{height}")
        crop = source.crop(applied).convert("RGB")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    crop.save(args.output, format="PNG", optimize=True)
    record = {
        "src": args.src,
        "mimeType": "image/png",
        "alt": args.alt.strip(),
        "caption": args.caption.strip(),
        "sourcePage": args.source_page,
        "renderDpi": args.render_dpi,
        "cropBox": list(applied),
        "width": crop.width,
        "height": crop.height,
        "sha256": sha256_file(args.output),
        "reviewStatus": "unreviewed",
    }
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
