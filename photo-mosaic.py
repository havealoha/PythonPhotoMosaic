# photo-mosaic.py

import os
import random
import argparse
import numpy as np
from PIL import Image
from collections import defaultdict
import pickle
from pathlib import Path

# ====================== DEFAULTS ======================
DEFAULT_SOURCE    = "source.jpg"
DEFAULT_TILES     = "tiles" #put your small images here
DEFAULT_OUTPUT    = "mosaic_result.jpg"
DEFAULT_NO_REPEAT = 5
# =====================================================

def get_average_color(path):
    try:
        with Image.open(path) as im:
            im = im.convert("RGB").resize((100, 100), Image.LANCZOS)
            return tuple(np.array(im).mean(axis=(0,1)).astype(int))
    except Exception:
        return None

def build_database(tiles_folder):
    folder = Path(tiles_folder).expanduser().resolve()
    if not folder.is_dir():
        raise ValueError(f"Tiles folder does not exist: {folder}")

    exts = {'.jpg','.jpeg','.png','.webp','.bmp','.tiff','.gif','.heic','.avif','.svg'}
    files = [p for p in folder.iterdir() if p.suffix.lower() in exts and p.is_file()]

    print(f"Building database from {len(files)} images in:\n  {folder}")
    db = defaultdict(list)
    for p in files:
        col = get_average_color(p)
        if col:
            db[str(col)].append(str(p.absolute()))
    print(f"Database ready — {len(db)} colors · {sum(len(v) for v in db.values())} tiles")
    return db

def save_db(db, path):
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'wb') as f:
        pickle.dump(dict(db), f)
    print(f"Cache saved → {p}")

def load_db(path):
    if not path:
        return None
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return None
    try:
        with open(p, 'rb') as f:
            data = pickle.load(f)
        print(f"Cache loaded → {p} ({len(data)} colors)")
        return defaultdict(list, data)
    except Exception as e:
        print(f"Failed to load cache ({e})")
        return None

def create_mosaic(source, db, output, no_repeat=5, tile_size=16, scale=8):
    src = Path(source).expanduser().resolve()
    print(f"Source → {src}")

    with Image.open(src) as img:
        img = img.convert("RGB")

    gw = img.width // tile_size
    gh = img.height // tile_size
    small = img.resize((gw, gh), Image.LANCZOS)

    W = gw * tile_size * scale
    H = gh * tile_size * scale
    mosaic = Image.new("RGB", (W, H))

    used = [[None] * gw for _ in range(gh)]
    pixels = np.array(small)
    total = gw * gh
    i = 0

    print("Rendering mosaic with maximum variety...")
    for y in range(gh):
        for x in range(gw):
            i += 1
            target = tuple(pixels[y, x])
            cand = db.get(str(target), []).copy()

            if len(cand) < 10:
                similar = sorted(db.keys(),
                    key=lambda k: np.linalg.norm(np.array(target) - np.array(eval(k))))[:50]
                for k in similar:
                    cand.extend(db[k])
                    if len(cand) >= 400: break

            if no_repeat > 0 and cand:
                banned = set()
                r = no_repeat
                for dy in range(-r, r+1):
                    for dx in range(-r, r+1):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < gw and 0 <= ny < gh and used[ny][nx]:
                            banned.add(used[ny][nx])
                cand = [c for c in cand if c not in banned]

            if not cand:
                all_tiles = [t for sub in db.values() for t in sub]
                cand = random.sample(all_tiles, min(30, len(all_tiles)))

            chosen = random.choice(cand)
            used[y][x] = chosen

            with Image.open(chosen) as tile:
                tile = tile.convert("RGB").resize((tile_size*scale, tile_size*scale), Image.LANCZOS)
                mosaic.paste(tile, (x*tile_size*scale, y*tile_size*scale))

            if i % max(1, total//40) == 0:
                print(f"  {i}/{total} tiles placed")

    out = Path(output).expanduser().resolve()
    mosaic.save(out, quality=95, subsampling=0)
    print(f"\nSUCCESS → {out}")

# ====================== CLI ======================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ultimate Photomosaic Tool — Full Path Freedom")
    parser.add_argument("-s", "--source",    help="Source image (e.g. photo.webp)")
    parser.add_argument("-t", "--tiles",     default=DEFAULT_TILES, help="Tiles folder (supports ./tiles, ../pics, etc.)")
    parser.add_argument("-o", "--output",    default=DEFAULT_OUTPUT, help="Output file")
    parser.add_argument("--db", "--cache",   dest="db", help="Exact database/cache file to use or create")
    parser.add_argument("--build-db",        action="store_true", help="Force rebuild database")
    parser.add_argument("--no-repeat", type=int, default=DEFAULT_NO_REPEAT,
                        help=f"Anti-repeat radius (0–12, default {DEFAULT_NO_REPEAT})")
    parser.add_argument("--scale",           type=int, default=8, help="Final tile size multiplier (default 8)")

    args = parser.parse_args()

    # Resolve paths
    source_path = args.source or DEFAULT_SOURCE
    tiles_path = args.tiles

    # DB logic — you have full control
    if args.db:
        db_path = args.db
    else:
        db_path = os.path.join(tiles_path, ".photomosaic_cache.pkl")

    # Load or build
    db = None
    if not args.build_db:
        db = load_db(db_path)

    if db is None:
        db = build_database(tiles_path)
        save_db(db, db_path)

    create_mosaic(
        source=source_path,
        db=db,
        output=args.output,
        no_repeat=args.no_repeat,
        scale=args.scale
    )
