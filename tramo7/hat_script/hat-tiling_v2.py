# tiling algorithm by Maxim Shtuchka
import math
import time

from shapely.geometry import Polygon, MultiPolygon, MultiPoint, Point
from shapely import affinity, polygons
from shapely import polygons as shp_polys
from shapely.geometry import JOIN_STYLE

import sys
from pathlib import Path

# Add the project root directory to Python path
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

from polygon_utils import (
    center_rectangle_on_polygons,
    is_polygon_inside_frame,
    export_polygons_to_svg,
    crosses_boundary,
    simple_svg_save,
)

from load_hole_polygons import get_hole_points

# Build hat tiles in grid coordinates using integers
# Rotate/translate using grid operations (integers)
# Attach blocks by searching integer translations
# Convert to world coordinates using the basis vectors x and y
# Render to SVG using Cartesian coordinates
# The 0.4 scale factor controls the final size, and the 60° rotation aligns the output with the tile geometry.


def add(v1,v2):
    return (v1[0]+v2[0],v1[1]+v2[1])

def sub(v1,v2):
    return (v1[0]-v2[0],v1[1]-v2[1])

def scale(k,v):
    return (v[0]*k,v[1]*k)

def rotate_60(v):
    sin=math.sin(math.pi/3)
    cos=math.cos(math.pi/3)
    return (v[0]*cos+v[1]*sin,v[1]*cos-v[0]*sin)

def flip_polygon_in_grid(polygon):
    return reversed([(x+y,-y) for (x,y) in polygon])

def rotate_polygon_in_grid(polygon,count):
    for c in range(count):
        polygon=[(-y,x+y) for (x,y) in polygon]
    return polygon

def rotate_polygons_in_grid(polygons,count):
    return [rotate_polygon_in_grid(p,count) for p in polygons]

def translate_polygon_in_grid(polygon,shift):
    return [(x+shift[0],y+shift[1]) for (x,y) in polygon]

def translate_polygons_in_grid(polygons,shift):
    return [translate_polygon_in_grid(p,shift) for p in polygons]

def convert_vertex_to_world_cs(vertex,origin,x,y):
    return add(origin,add(scale(vertex[0],x),scale(vertex[1],y)))

def convert_polygon_to_world_cs(polygon,origin,x,y):
    return [convert_vertex_to_world_cs(v,origin,x,y) for v in polygon]

def convert_polygons_to_world_cs(polygons,origin,x,y):
    return [convert_polygon_to_world_cs(p,origin,x,y) for p in polygons]

def get_contour_edge(contour,edge_index):
    return (contour[edge_index],contour[(edge_index+1)%len(contour)])

def are_nodes_equal(node1,node2):
    return node1[0]==node2[0] and node1[1]==node2[1]

def are_edges_equal(edge1,edge2):
    return are_nodes_equal(edge1[0],edge2[0]) and are_nodes_equal(edge1[1],edge2[1])

def count_common_contour_points(contour1,contour2):
    set1=set(contour1)
    count=0
    for v in contour2:
        if v in set1:
            count+=1
    return count

def get_single_border_contour(polygons):
    edges=set()
    for polygon in polygons:
        for edge_index in range(len(polygon)):
            edge=get_contour_edge(polygon,edge_index)
            opposite_edge=(edge[1],edge[0])
            if opposite_edge in edges:
                edges.remove(opposite_edge)
            else:
                edges.add(edge)
    contour=[next(iter(edges))[0]]
    while True:
        next_edge=None
        for e in edges:
            if e[0]==contour[-1]:
                next_edge=e
                break
        if next_edge is None:
            return None
        contour.append(next_edge[1])
        edges.remove(next_edge)
        if are_nodes_equal(contour[-1],contour[0]):
            contour.pop()
            break
    if len(edges)!=0:
        return None
    return contour

def make_hat_in_grid():
    return [
        (0,0),
        (0,3),
        (2,2),
        (3,3),
        (6,0),
        (6,-3),
        (8,-4),
        (9,-6),
        (6,-6),
        (3,-3),
        (2,-4),
        (0,-3),
        (-2,-2),
        (-3,0)
    ]

def make_first_block(add_ear):
    result=[
        make_hat_in_grid(),
        translate_polygon_in_grid(rotate_polygon_in_grid(flip_polygon_in_grid(make_hat_in_grid()),3),(6,-6)),
        translate_polygon_in_grid(rotate_polygon_in_grid(make_hat_in_grid(),4),(0,-6)),
        translate_polygon_in_grid(rotate_polygon_in_grid(make_hat_in_grid(),5),(0,-12)),
        translate_polygon_in_grid(rotate_polygon_in_grid(make_hat_in_grid(),6),(6,-12)),
        translate_polygon_in_grid(rotate_polygon_in_grid(make_hat_in_grid(),7),(12,-12)),
        translate_polygon_in_grid(rotate_polygon_in_grid(make_hat_in_grid(),8),(12,-6)),
    ]
    if add_ear:
        result.append(translate_polygon_in_grid(rotate_polygon_in_grid(make_hat_in_grid(),6),(6,-18)))
    return result

def attach_block(main,new,print_translation):
    #return main+new
    main_contour=get_single_border_contour(main)
    new_contour=get_single_border_contour(new)
    for distance in range(1000):
        for dx in range(-distance,distance+1):
            for dy in range(-distance,distance+1):
                if dx+dy>distance or dx+dy<-distance:
                    continue
                if abs(dx)!=distance and abs(dy)!=distance and abs(dx+dy)!=distance:
                    continue
                candidate_contour=translate_polygon_in_grid(new_contour,(dx,dy))
                min_acceptable_common_length=len(candidate_contour)/5
                if count_common_contour_points(main_contour,candidate_contour)<min_acceptable_common_length+1:
                    continue
                candidate=translate_polygons_in_grid(new,(dx,dy))
                combined=main+candidate
                combined_contour=get_single_border_contour(combined)
                if combined_contour is None:
                    continue
                common_length=(len(main_contour)+len(candidate_contour)-len(combined_contour))/2
                if common_length<min_acceptable_common_length:
                    continue
                if print_translation:
                    print(dx,",",dy)
                return combined
    raise ValueError("unable to attach a contour")

def make_second_block(add_ear):
    full_first_block=make_first_block(True)
    result=full_first_block
    result=attach_block(result,translate_polygons_in_grid(make_first_block(False),(-6,18)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_first_block,4),(-6,0)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_first_block,5),(-6,-12)),False)
    if add_ear:
        result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_first_block,6),(6,-24)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_first_block,7),(12,0)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_first_block,8),(12,12)),False)
    return result

def make_third_block(add_ear):
    full_second_block=make_second_block(True)
    result=full_second_block
    result=attach_block(result,translate_polygons_in_grid(make_second_block(False),(-12,42)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_second_block,4),(-48,30)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_second_block,5),(-36,-24)),False)
    if add_ear:
        result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_second_block,6),(18,-66)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_second_block,7),(42,12)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_second_block,8),(30,66)),False)
    return result

def make_fourth_block(add_ear):
    full_third_block=make_third_block(True)
    result=full_third_block
    result=attach_block(result,translate_polygons_in_grid(make_third_block(False),(-30,108)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_third_block,4),(-156,108)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_third_block,5),(-114,-54)),False)
    if add_ear:
        result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_third_block,6),(48,-174)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_third_block,7),(120,42)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_third_block,8),(78,204)),False)
    return result

def make_fifth_block(add_ear):
    full_fourth_block=make_fourth_block(True)
    result=full_fourth_block
    result=attach_block(result,translate_polygons_in_grid(make_fourth_block(False),(-78,282)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,4),(-438,312)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,5),(-318,-132)),False)
    if add_ear:
        result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,6),(126,-456)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,7),(324,120)),False)
    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,8),(204,564)),False)
    return result

def make_partial_fifth_block(add_ear):
    full_fourth_block=make_fourth_block(True)
    result=full_fourth_block
    result=attach_block(result,translate_polygons_in_grid(make_fourth_block(False),(-78,282)),False)
    # result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,4),(-438,312)),False)
    return result

def make_sixth_block(add_ear):
    full_fifth_block=make_fifth_block(True)
    result=full_fifth_block
    result=attach_block(result,translate_polygons_in_grid(make_fifth_block(False),(-204,738)),True)
    # result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,4),(-438,312)),True)
    #result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,5),(-318,-132)),True)
    #if add_ear:
    #    result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,6),(126,-456)),True)
    #result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,7),(324,120)),True)
    #result=attach_block(result,translate_polygons_in_grid(rotate_polygons_in_grid(full_fourth_block,8),(204,564)),True)
    return result


origin=[350.,350.]
origin=[-100.,-1400.] # adhoc translation
x=(0, 7.1) # scaling factor
y=rotate_60(x)
start=time.time()

# polygons=make_second_block(True)
# polygons=make_third_block(True)
# polygons=make_fourth_block(True)
# polygons=make_fifth_block(True)
tessellation_polygons=make_partial_fifth_block(True)
# polygons=make_sixth_block(True)

polygons_world_cs = convert_polygons_to_world_cs(tessellation_polygons, origin, x, y)
hat_polygons = [Polygon(p) for p in polygons_world_cs]
hole_polygons = [Polygon(p) for p in get_hole_points()]

print(" =>translating holes to origin (0,0)")

for poly in hole_polygons:
    if (poly.area < 400) and (len(poly.exterior.coords) > 10):
        # it is the 1/4-circle hole
        # we correct the position of the hole
        circle_hole = affinity.translate(poly, -3.1470695, -1.4994994)
        hole_polygons.remove(poly)

hole_polygons.append(circle_hole)
holes_group = MultiPolygon(hole_polygons)

# send holes (as a MultiPolygon)to the origin
x_to_origin, y_to_origin = (-holes_group.centroid.coords[0][0], -holes_group.centroid.coords[0][1])
origin_holes = affinity.translate(holes_group, x_to_origin, y_to_origin) 


def get_hat_orientation(hat_polygon, n1, n2):
    # we create a vector between points 1 and n
    # and calculate the arctangent to find the orientation
    # of the hat.  This provides a value which uniquely
    # identifies each hat in the collection of possibilities
    h1 = hat_polygon.exterior.coords[n1]
    hn = hat_polygon.exterior.coords[n2]
    dx,dy = (hn[0]-h1[0], hn[1]-h1[1])
    angle = round(math.atan2(dy,dx),4)
    return angle

# created in a jupyter solve.it notebook
# by matching get_hat_orientation to the configurations 
# cf. hat_configurations.svg for an illustration
orientation_dict = {
    -2.9515: (0, False),
 2.2845: (60, False),
 1.2373: (120, False),
  0.1901: (180, False),
 -0.8571: (240, False),
 -1.9043: (300, False),
 0.1562: (0, True),
 0.8571: (60, True),
 1.2034: (60, True),
 2.2506: (120, True),
 -2.9854: (180, True),
 -1.9382: (240, True),
 -0.891: (300, True)}


def mirror_holes(origin_holes):
    # assumes origin holes are a MultiPolygon
    # creates a mirror image of the holes
    mirror_group = []
    for poly in origin_holes.geoms:
        mirror_poly = []
        for coor in poly.exterior.coords:
            mirror_poly.append((-coor[0], coor[1]))
        mirror_group.append(Polygon(mirror_poly))
    return MultiPolygon(mirror_group)


# Create Frame to select region of interest
frame = shp_polys([[0,0],
                  [0 + 1400, 0],
                  [0 + 1400, 0 + 2000],
                  [0, 0 + 2000]])

# Keep only polygons inside selected frame
# create frame
centered_frame = center_rectangle_on_polygons(hat_polygons, frame)


# keep only polygons inside selected frame
filtered_hat_polygons = [polygon for polygon in hat_polygons if \
    is_polygon_inside_frame(polygon, centered_frame)]


def assemble_hats_and_holes(hat_polygons, origin_holes):
    final_polygon_list = []
    for k, hat_poly in enumerate(hat_polygons):
        hat_orient = get_hat_orientation(hat_poly,0, 7)
        hat_x, hat_y = hat_poly.centroid.xy
        if hat_orient not in orientation_dict:
            print(f"{k} --> {hat_orient} not in orientation_dict")
            # this polygon has no valid orientation
            # probably because the starting point is not the first point
            final_polygon_list.append(hat_poly)
            continue
        transform = orientation_dict[hat_orient]

        if transform[1]:
            # it's a mirror tile
            holes = mirror_holes(origin_holes)
            rot_holes = affinity.rotate(holes, angle=transform[0], origin="centroid")
        else:
            holes = origin_holes
            rot_holes = affinity.rotate(holes, angle=-transform[0], origin="centroid")
        
        tran_holes = affinity.translate(rot_holes, hat_x, hat_y)
        final_polygon_list.append(tran_holes)
        final_polygon_list.append(hat_poly)
    return final_polygon_list

## FINAL ASSEMBLY OF HATS AND HOLES
# final_polygon_list = assemble_hats_and_holes(filtered_hat_polygons, origin_holes)

    

INSET_DISTANCE = 3.2   # X ratio gives gaps of about 2Xmm solid channels
inset_polygon_list = []
for poly in filtered_hat_polygons:
    # mitre join style is used to keepsharp corners
    inset_polygon_list.append(poly.buffer(-INSET_DISTANCE, join_style=JOIN_STYLE.mitre))    

def add_tile(tile_width, tile_height, polygon_list, up_shift=0):
    # create tile, center it on the polygons
    tile = shp_polys([[0,0],
                  [0 + tile_width, 0],
                  [0 + tile_width, 0 + tile_height],
                  [0, 0 + tile_height]])
    
    # calculate horizontal span /middle of polygons
    left_most_polygon = min(polygon_list, key=lambda x: x.bounds[0])
    right_most_polygon = max(polygon_list, key=lambda x: x.bounds[2])
    
    middle_of_polygons = (left_most_polygon.bounds[0] + right_most_polygon.bounds[2])/2
    middle_of_tile = (tile.bounds[0] + tile.bounds[2])/2
    shift_to_edge =  left_most_polygon.bounds[0] - tile.bounds[0] 
    tile = affinity.translate(tile, shift_to_edge, up_shift)

    middle_of_tile = (tile.bounds[0] + tile.bounds[2])/2
    shift_to_middle = middle_of_polygons - middle_of_tile
    tile = affinity.translate(tile, shift_to_middle, 0)
    
    return tile

def add_inner_tile(outer_tile, endtile=False):
    if endtile:
        TILE_BOTTOM_MARGIN = 10
        INNER_TILE_HEIGHT = 170
    else:
        TILE_BOTTOM_MARGIN = 26
        INNER_TILE_HEIGHT = 120
    
    TILE_SIDE_MARGIN = 16
    outer_tile_width = outer_tile.bounds[2] - outer_tile.bounds[0]
    bottom_left_point = outer_tile.exterior.coords[0]

    inner_tile = shp_polys([[bottom_left_point[0] + TILE_SIDE_MARGIN, 
                            bottom_left_point[1] + TILE_BOTTOM_MARGIN],
                              [bottom_left_point[0] + outer_tile_width - TILE_SIDE_MARGIN, 
                              bottom_left_point[1] + TILE_BOTTOM_MARGIN],
                              [bottom_left_point[0] + outer_tile_width - TILE_SIDE_MARGIN, 
                              bottom_left_point[1] + INNER_TILE_HEIGHT + TILE_BOTTOM_MARGIN],
                              [bottom_left_point[0] + TILE_SIDE_MARGIN, 
                              bottom_left_point[1] + INNER_TILE_HEIGHT + TILE_BOTTOM_MARGIN]])
    
    return inner_tile

tile_721 = add_tile(1130, 170, filtered_hat_polygons, up_shift=-2000)
inner_tile_721 = add_inner_tile(tile_721)

tile_722 = add_tile(803, 170, filtered_hat_polygons, up_shift=tile_721.bounds[3] + 7)
inner_tile_722 = add_inner_tile(tile_722)

tile_723 = add_tile(865, 170, filtered_hat_polygons, up_shift=tile_722.bounds[3] + 7)
inner_tile_723 = add_inner_tile(tile_723)

tile_724 = add_tile(1135, 170, filtered_hat_polygons, up_shift=tile_723.bounds[3] + 7)
inner_tile_724 = add_inner_tile(tile_724)

tile_725 = add_tile(905, 170, filtered_hat_polygons, up_shift=tile_724.bounds[3] + 7)
inner_tile_725 = add_inner_tile(tile_725)

tile_726 = add_tile(905, 170, filtered_hat_polygons, up_shift=tile_725.bounds[3] + 7)
inner_tile_726 = add_inner_tile(tile_726)

tile_727 = add_tile(905, 170, filtered_hat_polygons, up_shift=tile_726.bounds[3] + 7)
inner_tile_727 = add_inner_tile(tile_727)

tile_728 = add_tile(905, 170, filtered_hat_polygons, up_shift=tile_727.bounds[3] + 7)
inner_tile_728 = add_inner_tile(tile_728)

tile_729 = add_tile(905, 190, filtered_hat_polygons, up_shift=tile_728.bounds[3] + 7)
inner_tile_729 = add_inner_tile(tile_729, endtile=True)

tiles_and_frames = filtered_hat_polygons
tiles_and_frames = []
tiles_and_frames.extend([tile_721] + [inner_tile_721])
tiles_and_frames.extend([tile_722] + [inner_tile_722] + [tile_723] + [inner_tile_723])
tiles_and_frames.extend([tile_724] + [inner_tile_724])
tiles_and_frames.extend([tile_725] + [inner_tile_725])
tiles_and_frames.extend([tile_726] + [inner_tile_726])
tiles_and_frames.extend([tile_727] + [inner_tile_727])
tiles_and_frames.extend([tile_728] + [inner_tile_728])
tiles_and_frames.extend([tile_729] + [inner_tile_729])



def crop_and_save_tile(polygons, tile, inner_tile, tile_name, save_holes=True):
    cropped_polygons = []
    # keep only the holes
    if save_holes:
        # keep only holes
        polygons = [poly for poly in polygons if poly.geom_type == 'MultiPolygon']
    else:
        # keep only lines
        polygons = [poly for poly in polygons if poly.geom_type == 'Polygon']
    for poly in polygons:
        if crosses_boundary(poly, inner_tile):
            result = poly.intersection(inner_tile)
            if isinstance(result, MultiPolygon):
                cropped_polygons.extend(result.geoms)
            elif isinstance(result, MultiPoint):
                cropped_polygons.append(poly)
            elif isinstance(result, Point):
                # if only one point in common and centroid outside of inner tile
                if not inner_tile.contains(result.centroid):
                    continue
            else:
                cropped_polygons.append(result)
        elif inner_tile.contains(poly):
            cropped_polygons.append(poly)
        else:
            continue
    return cropped_polygons + [tile]

crop_hats_721 = crop_and_save_tile(inset_polygon_list, tile_721, inner_tile_721, "721_hats", save_holes=False)
crop_hats_722 = crop_and_save_tile(inset_polygon_list, tile_722, inner_tile_722, "722_hats", save_holes=False)
crop_hats_723 = crop_and_save_tile(inset_polygon_list, tile_723, inner_tile_723, "723_hats", save_holes=False)
crop_hats_724 = crop_and_save_tile(inset_polygon_list, tile_724, inner_tile_724, "724_hats", save_holes=False)
crop_hats_725 = crop_and_save_tile(inset_polygon_list, tile_725, inner_tile_725, "725_hats", save_holes=False)
crop_hats_726 = crop_and_save_tile(inset_polygon_list, tile_726, inner_tile_726, "726_hats", save_holes=False)
crop_hats_727 = crop_and_save_tile(inset_polygon_list, tile_727, inner_tile_727, "727_hats", save_holes=False)
crop_hats_728 = crop_and_save_tile(inset_polygon_list, tile_728, inner_tile_728, "728_hats", save_holes=False)
crop_hats_729 = crop_and_save_tile(inset_polygon_list, tile_729, inner_tile_729, "729_hats", save_holes=False)

final_export_list = crop_hats_721 + crop_hats_722 + crop_hats_723 + \
    crop_hats_724 + crop_hats_725 + crop_hats_726 + crop_hats_727 + \
        crop_hats_728 + crop_hats_729
# Export and save to SVG
# export_polygons_to_svg(cropped_polygons + [tile_721] + [inner_tile_721], f"{str(script_dir)}/tramo7.2.svg")

export_polygons_to_svg(filtered_hat_polygons + [centered_frame], f"{str(script_dir)}/tramo7.2_frame.svg")
# export_polygons_to_svg(final_polygon_list, f"{str(script_dir)}/full_polygons.svg")
# simple_svg_save(final_polygon_list + tiles_and_frames,
#                 f"{str(script_dir)}/full_polygons_test.svg", label=False)

simple_svg_save(inset_polygon_list + tiles_and_frames,
                f"{str(script_dir)}/inset_polygons_test.svg", label=False)

print("before cleanup: ",len(final_export_list))
# Filter out small polygons - use list comprehension to avoid iteration bug
# Also check that geometry has .area attribute (Polygon, MultiPolygon have it, but Point/LineString don't)
final_export_list = [
    p for p in final_export_list 
    if hasattr(p, 'area') and p.area >= 16
]
print("after cleanup: ",len(final_export_list))

simple_svg_save(final_export_list, f"{str(script_dir)}/final_export_list.svg", label=False)

print("polygon count: ",len(tessellation_polygons))
print("time:",time.time()-start)

