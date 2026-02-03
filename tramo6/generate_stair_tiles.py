"""
Example script showing how to use penrose_p2.py to generate Shapely polygons.

This demonstrates the new export functionality added to the Penrose tiling generator.
"""
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

from penrose_tessellation import iterate, SUN, Vec2, get_shapely_polygons

# Example 1: Generate tiles and convert to Shapely polygons
print("Example 1: Generate Shapely polygons directly")
print("-" * 50)

# Start with a SUN pattern and iterate 3 times
initial_tiles = [t.translate(Vec2(800, 500)) for t in SUN]
tiles = iterate(initial_tiles, iters=7)

# Convert to Shapely polygons
polygons = get_shapely_polygons(tiles)
print(f"Generated {len(polygons)} Shapely polygons")

# translate polygons to center of page:
polygons = [affinity.translate(poly, xoff=100, yoff=-1600) for poly in polygons]

# Create Frame to select region of interest
frame = Polygon([[0,0],
                 [0 + 1000, 0],
                 [0 + 1000, 0 + 1800],
                 [0, 0 + 1800]])

# create frame
# centered_frame = center_rectangle_on_polygons(polygons, frame)
centered_frame = center_frame(polygons, frame)

# keep only polygons inside selected frame
filtered_polygons = [polygon for polygon in polygons if \
     is_polygon_inside_frame(polygon, centered_frame)]

INSET_DISTANCE_KITE = 4.2   # 3.2 X ratio gives gaps of about 2Xmm solid channels
INSET_DISTANCE_DART = 3.2
inset_polygon_list = []
for poly in filtered_polygons:
    # mitre join style is used to keepsharp corners
    if poly.area > 500: # kite
        inset_polygon_list.append(poly.buffer(-INSET_DISTANCE_KITE, join_style=JOIN_STYLE.mitre))    
    else: # dart
        inset_polygon_list.append(poly.buffer(-INSET_DISTANCE_DART, join_style=JOIN_STYLE.mitre))    

filtered_polygons = inset_polygon_list

# tile_511 = add_tile(908, 168, filtered_polygons, center_tile=True, up_shift=centered_frame.bounds[1] + 5)
# inner_tile_511 = add_inner_tile(tile_511)

INITIAL_UPSHIFT = 100
NEXT_UPSHIFT = 4 # 2 4 

tile_711 = add_tile(908, 172, filtered_polygons, center_tile=True, up_shift=centered_frame.bounds[1] + INITIAL_UPSHIFT)
inner_tile_711 = add_inner_tile(tile_711)

tile_712 = add_tile(908, 172, filtered_polygons, center_tile=True, up_shift=tile_711.bounds[3] + NEXT_UPSHIFT)
inner_tile_712 = add_inner_tile(tile_712)

tile_713 = add_tile(908, 172, filtered_polygons, center_tile=True, up_shift=tile_712.bounds[3] + NEXT_UPSHIFT )
inner_tile_713 = add_inner_tile(tile_713)

tile_714 = add_tile(908, 172, filtered_polygons, center_tile=True, up_shift=tile_713.bounds[3] + NEXT_UPSHIFT)
inner_tile_714 = add_inner_tile(tile_714)

tile_715 = add_tile(908, 172, filtered_polygons, center_tile=True, up_shift=tile_714.bounds[3] + NEXT_UPSHIFT)
inner_tile_715 = add_inner_tile(tile_715)

tile_716 = add_tile(908, 172, filtered_polygons, center_tile=True, up_shift=tile_715.bounds[3] + NEXT_UPSHIFT)
inner_tile_716 = add_inner_tile(tile_716)

tile_717 = add_tile(908, 172, filtered_polygons, center_tile=True, up_shift=tile_716.bounds[3] + NEXT_UPSHIFT)
inner_tile_717 = add_inner_tile(tile_717)

tile_718 = add_tile(908, 172, filtered_polygons, center_tile=True, up_shift=tile_717.bounds[3] + NEXT_UPSHIFT)
inner_tile_718 = add_inner_tile(tile_718)

tile_719 = add_tile(908, 172, filtered_polygons, center_tile=True, up_shift=tile_718.bounds[3] + NEXT_UPSHIFT)
inner_tile_719 = add_inner_tile(tile_719)

final_polygon_list = inset_polygon_list + [tile_711] + [inner_tile_711] + \
    [tile_712] + [inner_tile_712] + [tile_713] + [inner_tile_713] + \
    [tile_714] + [inner_tile_714] + [tile_715] + [inner_tile_715] + \
    [tile_716] + [inner_tile_716] + [tile_717] + [inner_tile_717] + \
    [tile_718] + [inner_tile_718] + [tile_719] + [inner_tile_719] + \
    [centered_frame]

simple_svg_save(final_polygon_list, f"{str(script_dir)}/penrose_tiles.svg", label=False)

# crop tiles at the edge of a tile frame 
crop_711 = crop_and_save_tile(filtered_polygons, inner_tile_711, save_holes=False)
crop_712 = crop_and_save_tile(filtered_polygons, inner_tile_712, save_holes=False)
crop_713 = crop_and_save_tile(filtered_polygons, inner_tile_713, save_holes=False)
crop_714 = crop_and_save_tile(filtered_polygons, inner_tile_714, save_holes=False)
crop_715 = crop_and_save_tile(filtered_polygons, inner_tile_715, save_holes=False)
crop_716 = crop_and_save_tile(filtered_polygons, inner_tile_716, save_holes=False)
crop_717 = crop_and_save_tile(filtered_polygons, inner_tile_717, save_holes=False)
crop_718 = crop_and_save_tile(filtered_polygons, inner_tile_718, save_holes=False)
crop_719 = crop_and_save_tile(filtered_polygons, inner_tile_719, save_holes=False)

final_export_list = crop_711 + crop_712 + crop_713 + crop_714 + \
    crop_715 + crop_716 + crop_717 + crop_718 + crop_719 + \
    [centered_frame] + [tile_711] + [tile_712] + [tile_713] + \
    [tile_714] + [tile_715] + [tile_716] + [tile_717] + [tile_718] + [tile_719]

# remove holes that are too small
final_export_list = [
    p for p in final_export_list 
    if hasattr(p, 'area') and p.area >= 50
]
simple_svg_save(final_export_list, f"{str(script_dir)}/penrose_tiles_cropped.svg", label=False)

# Example: Filter polygons within a bounding box
# bbox = box(600, 300, 1000, 700)
# polygons_in_bbox = [p for p in scaled_polygons if bbox.intersects(p)]
#print(f"Polygons in bounding box: {len(polygons_in_bbox)}")

# Example: Buffer operation (expand/contract polygons)
# buffered = [p.buffer(5) for p in polygons[:5]]  # Buffer first 5 polygons
# print(f"Buffered {len(buffered)} polygons")


