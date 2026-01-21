import sys
import os
from pathlib import Path

from shapely.geometry import Polygon, JOIN_STYLE
from shapely import affinity

# Add the project root directory to Python path
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from polygon_utils import (
    is_polygon_inside_frame,
    simple_svg_save,
    center_frame,
    add_tile,
    add_inner_tile,
    crop_and_save_tile,
)


# Add the current directory to the path so we can import penrose_p2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Deflation import all_tiles


# convert all tiles to Shapely polygons
polygons = [Polygon(tile) for tile in all_tiles]
# scale all the polygons by 1000
polygons = [affinity.scale(poly, xfact=3000, yfact=3000, origin=(0,0)) for poly in polygons]
# translate polygons to center of page:
polygons = [affinity.translate(poly, xoff=-600, yoff=-3200) for poly in polygons]

# Create Frame to select region of interest
frame = Polygon([[0,0],
                 [0 + 1000, 0],
                 [0 + 1000, 0 + 1700],
                 [0, 0 + 1700]])

# create frame
# centered_frame = center_rectangle_on_polygons(polygons, frame)
centered_frame = center_frame(polygons, frame)

# keep only polygons inside selected frame
filtered_polygons = [polygon for polygon in polygons if \
     is_polygon_inside_frame(polygon, centered_frame)]

INSET_DISTANCE = 3   # X ratio gives gaps of about 2Xmm solid channels
inset_polygon_list = []
for poly in filtered_polygons:
    # mitre join style is used to keepsharp corners
    inset_polygon_list.append(poly.buffer(-INSET_DISTANCE, join_style=JOIN_STYLE.mitre))    

filtered_polygons = inset_polygon_list

print(centered_frame.bounds)

tile_511 = add_tile(908, 165, filtered_polygons, center_tile=True, up_shift=centered_frame.bounds[1] + 5)
inner_tile_511 = add_inner_tile(tile_511)

tile_512 = add_tile(908, 165, filtered_polygons, center_tile=True, up_shift=tile_511.bounds[3] + 7)
inner_tile_512 = add_inner_tile(tile_512)

tile_513 = add_tile(908, 165, filtered_polygons, center_tile=True, up_shift=tile_512.bounds[3] + 7)
inner_tile_513 = add_inner_tile(tile_513)

tile_514 = add_tile(908, 165, filtered_polygons, center_tile=True, up_shift=tile_513.bounds[3] + 7)
inner_tile_514 = add_inner_tile(tile_514)

tile_515 = add_tile(908, 165, filtered_polygons, center_tile=True, up_shift=tile_514.bounds[3] + 7)
inner_tile_515 = add_inner_tile(tile_515)

tile_516 = add_tile(908, 165, filtered_polygons, center_tile=True, up_shift=tile_515.bounds[3] + 7)
inner_tile_516 = add_inner_tile(tile_516)

tile_517 = add_tile(908, 165, filtered_polygons, center_tile=True, up_shift=tile_516.bounds[3] + 7)
inner_tile_517 = add_inner_tile(tile_517)

tile_518 = add_tile(908, 165, filtered_polygons, center_tile=True, up_shift=tile_517.bounds[3] + 7)
inner_tile_518 = add_inner_tile(tile_518)

tile_519 = add_tile(908, 184, filtered_polygons, center_tile=True, up_shift=tile_518.bounds[3] + 7)
inner_tile_519 = add_inner_tile(tile_519, endtile=True)

final_polygon_list = inset_polygon_list + \
[tile_511] + [inner_tile_511] + \
    [tile_512] + [inner_tile_512] + [tile_513] + [inner_tile_513] + \
    [tile_514] + [inner_tile_514] + [tile_515] + [inner_tile_515] + \
    [tile_516] + [inner_tile_516] + [tile_517] + [inner_tile_517] + \
    [tile_518] + [inner_tile_518] + [tile_519] + [inner_tile_519] + \
    [centered_frame]

# simple_svg_save(final_polygon_list, f"{str(script_dir)}/p1_section5_tiles.svg", label=False)

# crop tiles at the edge of a tile frame 
crop_511 = crop_and_save_tile(filtered_polygons, inner_tile_511, save_holes=False)
crop_512 = crop_and_save_tile(filtered_polygons, inner_tile_512, save_holes=False)
crop_513 = crop_and_save_tile(filtered_polygons, inner_tile_513, save_holes=False)
crop_514 = crop_and_save_tile(filtered_polygons, inner_tile_514, save_holes=False)
crop_515 = crop_and_save_tile(filtered_polygons, inner_tile_515, save_holes=False)
crop_516 = crop_and_save_tile(filtered_polygons, inner_tile_516, save_holes=False)
crop_517 = crop_and_save_tile(filtered_polygons, inner_tile_517, save_holes=False)
crop_518 = crop_and_save_tile(filtered_polygons, inner_tile_518, save_holes=False)
crop_519 = crop_and_save_tile(filtered_polygons, inner_tile_519, save_holes=False)

final_export_list = crop_511 + crop_512 + crop_513 + crop_514 + \
    crop_515 + crop_516 + crop_517 + crop_518 + crop_519 + [centered_frame] + \
    [tile_511] + [tile_512] + [tile_513] + [tile_514] + [tile_515] + \
        [tile_516] + [tile_517] + [tile_518] + [tile_519]
    

# remove holes that are too small
final_export_list = [
    p for p in final_export_list 
    if hasattr(p, 'area') and p.area >= 21
]

simple_svg_save(final_export_list, f"{str(script_dir)}/p1_section5_tiles_cropped.svg", label=False)


