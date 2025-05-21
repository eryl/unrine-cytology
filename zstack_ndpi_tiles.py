import os
import numpy as np
import cv2
from PIL import Image
import openslide
from glob import glob
from pathlib import Path

def get_z_plane_count(slide: openslide.OpenSlide) -> int:
    z_planes = 0
    while True:
        try:
            slide.get_best_level_for_downsample(1.0)  # ensure initialized
            slide.read_region((0, 0), 0, (1, 1), z=z_planes)
            z_planes += 1
        except TypeError:
            break
        except Exception:
            break
    return z_planes

def focus_score_laplacian(image):
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def zstack_focus(stack):
    scores = np.stack([cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), cv2.CV_64F).var(axis=(0, 1)) for img in stack])
    best = np.argmax(scores, axis=0)
    out = np.zeros_like(stack[0])
    for i, img in enumerate(stack):
        out[best == i] = img[best == i]
    return out

def process_ndpi_to_zstack_tiles(ndpi_path, output_dir, tile_size=2048, overlap=0):
    slide = openslide.OpenSlide(ndpi_path)
    basename = Path(ndpi_path).stem
    level = 0  # base resolution

    # Estimate number of Z-planes
    z_planes = get_z_plane_count(slide)
    if z_planes == 0:
        print(f"Warning: No z-stack planes found in {ndpi_path}")
        return

    w, h = slide.level_dimensions[level]
    stride = tile_size - overlap
    os.makedirs(output_dir, exist_ok=True)

    for y in range(0, h, stride):
        for x in range(0, w, stride):
            stack = []
            for z in range(z_planes):
                try:
                    region = slide.read_region((x, y), level, (tile_size, tile_size), z=z).convert("RGB")
                    stack.append(np.array(region))
                except Exception as e:
                    print(f"Skipping z={z} at ({x},{y}): {e}")
                    break
            if len(stack) < z_planes:
                continue
            stacked = zstack_focus(stack)
            tile_name = f"{basename}_y{y}_x{x}.png"
            Image.fromarray(stacked).save(os.path.join(output_dir, tile_name))

    slide.close()

# ------------------ Main Entry ------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Z-stack NDPI base layer into tiles with focus stacking.")
    parser.add_argument("input_dir", help="Folder containing .ndpi files")
    parser.add_argument("output_dir", help="Folder to save output PNGs")
    parser.add_argument("--tile_size", type=int, default=2048)
    parser.add_argument("--overlap", type=int, default=0)
    args = parser.parse_args()

    ndpi_files = sorted(glob(os.path.join(args.input_dir, "*.ndpi")))
    for f in ndpi_files:
        print(f"Processing {f}...")
        out_path = os.path.join(args.output_dir, Path(f).stem)
        process_ndpi_to_zstack_tiles(f, out_path, tile_size=args.tile_size, overlap=args.overlap)
