import os
import subprocess
import shutil
from pathlib import Path

def run_tiffsplit(tiff_path, temp_dir):
    """Run tiffsplit on the given file and store output in temp_dir."""
    os.makedirs(temp_dir, exist_ok=True)
    cmd = ["tiffsplit", tiff_path, os.path.join(temp_dir, "split_")]
    subprocess.run(cmd, check=True)

def organize_split_files(temp_dir, output_dir, base_name):
    """Move split TIFF files to final output directory with clearer names."""
    split_files = sorted(Path(temp_dir).glob("split_*.tif"))
    for idx, src in enumerate(split_files):
        dst_name = f"{base_name}_z{idx:03d}.tif"
        dst_path = os.path.join(output_dir, dst_name)
        shutil.move(str(src), dst_path)

def split_ome_tiff_zplanes(tiff_path, output_dir):
    base_name = Path(tiff_path).stem
    temp_dir = os.path.join(output_dir, f"__tmp_{base_name}")
    print(f"Splitting {base_name}...")

    try:
        run_tiffsplit(tiff_path, temp_dir)
        organize_split_files(temp_dir, output_dir, base_name)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def batch_split_ome_tiffs(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    ome_files = [f for f in Path(input_dir).glob("*.ome.tif*")]

    if not ome_files:
        print("No OME-TIFF files found.")
        return

    for f in ome_files:
        split_ome_tiff_zplanes(str(f), output_dir)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Losslessly split OME-TIFF Z-planes using tiffsplit.")
    parser.add_argument("input_dir", help="Directory containing .ome.tiff files")
    parser.add_argument("output_dir", help="Directory to store extracted Z-plane TIFFs")
    args = parser.parse_args()

    batch_split_ome_tiffs(args.input_dir, args.output_dir)
