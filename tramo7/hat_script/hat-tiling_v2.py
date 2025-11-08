# tiling algorithm by Maxim Shtuchka
import math
import time

import svgwrite
from shapely.geometry import Polygon, MultiPolygon, MultiPoint, Point
from shapely import affinity, centroid, polygons
from shapely import polygons as shp_polys

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
)

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

def write_svg(polygons,file_name):
    with open(file_name,"w") as file:
        file.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n")
        file.write("<svg\n")
        file.write("\tversion=\"1.1\"\n")
        file.write("\txmlns=\"http://www.w3.org/2000/svg\"\n")
        file.write("\txmlns:svg=\"http://www.w3.org/2000/svg\">\n")
        for polygon in polygons:
            file.write("\t<path fill=\"none\" stroke=\"black\" stroke-width=\"0.01\" d=\"\n")
            file.write("\t\tM"+str(polygon[0][0])+" "+str(polygon[0][1])+" L\n")
            for vertex in polygon[1:]:
                file.write("\t\t"+str(vertex[0])+" "+str(vertex[1])+"\n")
            file.write("\t\tZ\"/>\n")
        file.write("</svg>")





origin=[350.,350.]
x=(0, 7) # scaling factor
y=rotate_60(x)
start=time.time()

# polygons=make_second_block(True)
# polygons=make_third_block(True)
# polygons=make_fourth_block(True)
polygons=make_fifth_block(True)
# polygons=make_sixth_block(True)

polygons_world_cs = convert_polygons_to_world_cs(polygons,origin,x,y)
shapely_polygons = [Polygon(p) for p in polygons_world_cs]

# Create Frame to select region of interest
frame = shp_polys([[0,0],
                  [0 + 1300, 0],
                  [0 + 1300, 0 + 1900],
                  [0, 0 + 1900]])

# Keep only polygons inside selected frame
# create frame
centered_frame = center_rectangle_on_polygons(shapely_polygons, frame)
frame_shift_x = 660 # horizontal shift for frame adjustment
frame_shift_y = 250  # vertical shift for frame adjustment
centered_frame = affinity.translate(centered_frame, frame_shift_x, frame_shift_y)

# keep only polygons inside selected frame
filtered_shapely_polygons = [polygon for polygon in shapely_polygons if \
    is_polygon_inside_frame(polygon, centered_frame)]

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

tile_721 = add_tile(1130, 170, filtered_shapely_polygons)
inner_tile_721 = add_inner_tile(tile_721)

tile_722 = add_tile(803, 170, filtered_shapely_polygons, up_shift=tile_721.bounds[3] + 7)
inner_tile_722 = add_inner_tile(tile_722)

tile_723 = add_tile(865, 170, filtered_shapely_polygons, up_shift=tile_722.bounds[3] + 7)
inner_tile_723 = add_inner_tile(tile_723)

tile_724 = add_tile(1135, 170, filtered_shapely_polygons, up_shift=tile_723.bounds[3] + 7)
inner_tile_724 = add_inner_tile(tile_724)

tile_725 = add_tile(905, 170, filtered_shapely_polygons, up_shift=tile_724.bounds[3] + 7)
inner_tile_725 = add_inner_tile(tile_725)

tile_726 = add_tile(905, 170, filtered_shapely_polygons, up_shift=tile_725.bounds[3] + 7)
inner_tile_726 = add_inner_tile(tile_726)

tile_727 = add_tile(905, 170, filtered_shapely_polygons, up_shift=tile_726.bounds[3] + 7)
inner_tile_727 = add_inner_tile(tile_727)

tile_728 = add_tile(905, 170, filtered_shapely_polygons, up_shift=tile_727.bounds[3] + 7)
inner_tile_728 = add_inner_tile(tile_728)

tile_729 = add_tile(905, 190, filtered_shapely_polygons, up_shift=tile_728.bounds[3] + 7)
inner_tile_729 = add_inner_tile(tile_729, endtile=True)

tiles_and_frames = filtered_shapely_polygons
tiles_and_frames.extend([tile_721] + [inner_tile_721])
tiles_and_frames.extend([tile_722] + [inner_tile_722] + [tile_723] + [inner_tile_723])
tiles_and_frames.extend([tile_724] + [inner_tile_724])
tiles_and_frames.extend([tile_725] + [inner_tile_725])
tiles_and_frames.extend([tile_726] + [inner_tile_726])
tiles_and_frames.extend([tile_727] + [inner_tile_727])
tiles_and_frames.extend([tile_728] + [inner_tile_728])
tiles_and_frames.extend([tile_729] + [inner_tile_729])



def crop_and_save_tile(polygons, tile, inner_tile, tile_name):
    cropped_polygons = []
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

    export_polygons_to_svg(cropped_polygons + [tile] + [inner_tile], f"{str(script_dir)}/{tile_name}_tamo7.svg")

crop_and_save_tile(filtered_shapely_polygons, tile_721, inner_tile_721, "721")

# Export and save to SVG
# export_polygons_to_svg(cropped_polygons + [tile_721] + [inner_tile_721], f"{str(script_dir)}/tramo7.2.svg")
print(type(shapely_polygons), type([centered_frame]))
export_polygons_to_svg(filtered_shapely_polygons + [centered_frame], f"{str(script_dir)}/tramo7.2_frame.svg")
write_svg(
    polygons_world_cs,
    f"{str(script_dir)}/qqq.svg"
)

print("polygon count: ",len(polygons))
print("time:",time.time()-start)

