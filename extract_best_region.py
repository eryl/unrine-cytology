import argparse
import openslide
import numpy as np
import cv2
from PIL import Image
import os

def focus_score(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def extract_best_focus(input_path, output_path, region_size=(2048, 2048)):
    slide = openslide.OpenSlide(input_path)

    # Check if image has Z-planes (OpenSlide may not expose these directly)
    z_planes = slide.get_property("openslide.objective-power-count")
    if z_planes is None:
        print("Warning: Z-planes not available in OpenSlide. Assuming only 1.")
        z_planes = 1

    best_score = -1
    best_plane_img = None
    best_z = None

    # Note: OpenSlide itself may not expose Z-planes from NDPI directly;
    # if not, you'll need to use Bio-Formats via bfconvert or tifffile on an OME-TIFF
    # For demonstration, we simulate Z by checking different slide levels
    for level in range(slide.level_count):
        w, h = slide.level_dimensions[level]
        x = max(0, w // 2 - region_size[0] // 2)
        y = max(0, h // 2 - region_size[1] // 2)
        region = slide.read_region((x, y), level, region_size).convert("RGB")
        region_np = np.array(region)

        score = focus_score(region_np)
        print(f"Level {level}: Focus score = {score:.2f}")

        if score > best_score:
            best_score = score
            best_plane_img = region
            best_z = level

    print(f"\nBest focus at level {best_z} with score {best_score:.2f}")
    output_full_path = os.path.join(output_path, f"best_focus_level_{best_z}.tiff")
    best_plane_img.save(output_full_path)
    print(f"Saved best-focus plane to {output_full_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_directory")
    args = parser.parse_args()

    input_ndpi = args.input_file
    output_dir = args.output_directory
    extract_best_focus(input_ndpi, output_dir)
    
if __name__ == "__main__":
    main()
