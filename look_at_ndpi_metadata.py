from pathlib import Path

from opentile import OpenTile
from wsidicomizer import WsiDicomizer
folders = [
    Path('/mnt/cytology-data'),
]

for folder in folders:
    for ndpi_file in folder.rglob('*.ndpi'):
        with OpenTile.open(ndpi_file) as tiff:
            for index, level in enumerate(tiff.levels):
                print(f"{ndpi_file.name}: {index} {level.focal_plane}")