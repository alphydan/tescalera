import math
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon, box, MultiPoint, Point
from shapely import polygons as shp_polys
from shapely import centroid, affinity

import svgwrite
from svgwrite import mm


# Create Polygon
def create_regular_polygon(center_x, center_y, radius, nr_points):
    angle = 2 * math.pi / nr_points
    polygon_points = []

    for i in range(nr_points):
        x = center_x + radius * math.cos(i * angle)
        y = center_y + radius * math.sin(i * angle)
        polygon_points.append((x, y))

    return Polygon(polygon_points)

# Polt polygon dict
def plot_polygon_dict(polygons, colors=None, alphas=None):
    """
    Function to plot a dictionary of polygons
    :param polygons: dictionary of polygons to plot
           note that keys are used as labels
    """
    fig, ax = plt.subplots(figsize=(5, 5))

    if colors is None:
        colors = plt.cm.rainbow(np.linspace(0, 1, len(polygons)))
    if alphas is None:
        alphas = [0.1] * len(polygons)

    # for polygon, color, alpha in zip(polygons, colors, alphas):
    color_idx = 0
    for key, polygon in polygons.items():
        x, y = polygon.exterior.xy
        ctr = centroid(polygon)
        ax.plot(x, y, color=colors[color_idx])
        # ax.fill(x, y, alpha=alpha, color="white")
        ax.text(ctr.x, ctr.y, key, fontsize=12, ha='center', va='center')
        color_idx += 1

    ax.axis('equal')

# Polygon normalization helpers
def _ensure_iterable(polygons):
    if isinstance(polygons, Polygon):
        return [polygons]
    if isinstance(polygons, MultiPolygon):
        return list(polygons.geoms)
    return list(polygons)


def _flatten_polygons(polygons):
    flat_polygons = []
    for polygon in polygons:
        if isinstance(polygon, MultiPolygon):
            flat_polygons.extend(list(polygon.geoms))
        else:
            flat_polygons.append(polygon)
    return flat_polygons


# Plot polygon list
def plot_polygon_list(polygons, colors=None, alphas=None):
    fig, ax = plt.subplots(figsize=(5, 5))

    polygons = _flatten_polygons(_ensure_iterable(polygons))

    if colors is None:
        colors = plt.cm.rainbow(np.linspace(0, 1, len(polygons)))
    if alphas is None:
        alphas = [0.1] * len(polygons)

    for polygon, color, alpha in zip(polygons, colors, alphas):
        x, y = polygon.exterior.xy
        ax.plot(x, y, color=color)

    ax.axis('equal')
    plt.show()


# Plot polygon list
def blue_plot(polygons):
    fig, ax = plt.subplots(figsize=(10, 5))
    color = "blue"
    all_polys = _flatten_polygons(_ensure_iterable(polygons))
    for poly in all_polys:
        x, y = poly.exterior.xy
        ax.plot(x, y, color=color, linewidth=0.5)

    ax.axis('equal')
    plt.show()


def center_frame(polygons, frame):
    polygons = _flatten_polygons(_ensure_iterable(polygons))

    max_poly_y = max(polygons, key=lambda x: x.centroid.bounds[1])
    max_poly_x = max(polygons, key=lambda x: x.centroid.bounds[0])
    min_poly_y = min(polygons, key=lambda x: x.centroid.bounds[1])
    min_poly_x = min(polygons, key=lambda x: x.centroid.bounds[0])

    min_y = min_poly_y.centroid.bounds[1]
    min_x = min_poly_x.centroid.bounds[0]
    max_y = max_poly_y.centroid.bounds[1]
    max_x = max_poly_x.centroid.bounds[0]

    polygon_center = box(min_x, min_y, max_x, max_y).centroid
    frame_center = frame.centroid
    dx = polygon_center.x - frame_center.x
    dy = polygon_center.y - frame_center.y
    centered_frame = affinity.translate(frame, dx, dy)
    
    return centered_frame
    
# center bounding box around polygons
def center_rectangle_on_polygons(polygons, rectangle):
    # Calculate the bounding box of all polygons
    all_polygons = Polygon()
    for poly in polygons:
        all_polygons = all_polygons.union(poly)

    polygons_bbox = all_polygons.bounds

    # Calculate centroids
    polygons_centroid = box(*polygons_bbox).centroid
    rectangle_centroid = rectangle.centroid

    # Calculate the translation needed
    dx = polygons_centroid.x - rectangle_centroid.x
    dy = polygons_centroid.y - rectangle_centroid.y

    # Apply translation to the rectangle
    centered_rectangle = affinity.translate(rectangle, dx, dy)

    return centered_rectangle
   
# helper function to delete polygons that fall outside of frame
def is_polygon_inside_frame(polygon, rect):
    """Check if the centroid of a polygon is inside a rectangle."""
    x, y = polygon.centroid.x, polygon.centroid.y
    (rx1, ry1, rx2, ry2) = rect.bounds
    return rx1 <= x <= rx2 and ry1 <= y <= ry2

def crosses_boundary(poly, rect):
    """It returns True when both conditions are met:
      * not rect.contains(poly) → The polygon is NOT fully inside the rectangle*
      * not poly.intersection(rect).is_empty → The polygon DOES overlap with the rectangle*
      So it returns True only when the polygon partially overlaps - meaning it crosses the boundary.*
      It returns False when:
      * The polygon is fully inside (first condition fails)
      * The polygon is fully outside (second condition fails)
    """
    return not rect.contains(poly) and not poly.intersection(rect).is_empty


def save_polygon_list_to_svg(polygon_list, filename='tramo1.2.svg', size=('1200mm', '300mm')):
    # Create a new SVG drawing with 1mm = 1 user unit scale
    dwg = svgwrite.Drawing(filename, size=size, profile='full', viewBox=f"0 0 {size[0].replace('mm','')} {size[1].replace('mm','')}")
    
    polygon_list = _flatten_polygons(_ensure_iterable(polygon_list))

    #---------------------------------------
    # Find bounding box of all polygons
    all_coords = []
    for polygon in polygon_list:
        all_coords.extend(polygon.exterior.coords)
    min_x = min(x for x,y in all_coords)
    max_x = max(x for x,y in all_coords)
    min_y = min(y for x,y in all_coords)
    max_y = max(y for x,y in all_coords)
    
    # Calculate center offset to move polygons to canvas center
    poly_width = max_x - min_x
    poly_height = max_y - min_y
    canvas_width = float(size[0].replace('mm',''))
    canvas_height = float(size[1].replace('mm',''))
    
    x_offset = (canvas_width - poly_width)/2 - min_x
    y_offset = (canvas_height - poly_height)/2 # - min_y
    
    
    # Create a group for all paths & add transform to center the group
    group = dwg.g(fill='none', stroke='blue', 
                  stroke_width=0.5, 
                  transform=f'translate({x_offset},{y_offset})')

    # Calculate the maximum y-coordinate to use for flipping
    max_y = max(max(coord[1] for coord in polygon.exterior.coords) for polygon in polygon_list)
    
    # Iterate through the polygons in the list
    for polygon in polygon_list:
        # Extract coordinates from the Shapely polygon, flip the y-coordinate
        coords = [(coord[0], max_y - coord[1]) for coord in polygon.exterior.coords]

        # Create a path
        path = dwg.path(d=f'M {coords[0][0]},{coords[0][1]}')

        # Add line segments to the path
        for coord in coords[1:]:
            path.push(f'L {coord[0]},{coord[1]}')

        # Close the path
        path.push('Z')

        # Add the path to the group
        group.add(path)

    # Add the group to the drawing
    dwg.add(group)

    # Save the drawing
    dwg.save()

def export_polygons_to_svg(polygon_list, filename='tramo7.2.svg', size=('12000mm', '12000mm')):

    # Create a new SVG drawing with 1mm = 1 user unit scale
    dwg = svgwrite.Drawing(filename, size=size, profile='full', viewBox=f"0 0 {size[0].replace('mm','')} {size[1].replace('mm','')}")
    
    #---------------------------------------
    # Find bounding box of all polygons
    all_coords = []
    for polygon in polygon_list:
        if isinstance(polygon, Polygon):
            all_coords.extend(polygon.exterior.coords)
    min_x = min(x for x,y in all_coords)
    max_x = max(x for x,y in all_coords)
    min_y = min(y for x,y in all_coords)
    max_y = max(y for x,y in all_coords)
    
    # Calculate center offset to move polygons to canvas center
    poly_width = max_x - min_x
    poly_height = max_y - min_y
    canvas_width = float(size[0].replace('mm',''))
    canvas_height = float(size[1].replace('mm',''))
    
    x_offset = (canvas_width - poly_width)/2 - min_x
    y_offset = (canvas_height - poly_height)/2 # - min_y
    
    
    # Create a group for all paths & add transform to center the group
    group = dwg.g(fill='none', stroke='blue', 
                  stroke_width=0.3, 
                  transform=f'translate({x_offset},{y_offset})')

    # Calculate the maximum y-coordinate to use for flipping
    if isinstance(polygon, Polygon):
        # calculate only for polygons, ignore MultiPolygon
        max_y = max(max(coord[1] for coord in polygon.exterior.coords) \
            for polygon in polygon_list \
                if isinstance(polygon, Polygon))
    
    # Iterate through the polygons in the list
    for polygon in polygon_list:
        if isinstance(polygon, Polygon):
            # Extract coordinates from the Shapely polygon, flip the y-coordinate
            coords = [(coord[0], max_y - coord[1]) for coord in polygon.exterior.coords]

            # Create a path
            path = dwg.path(d=f'M {coords[0][0]},{coords[0][1]}')

            # Add line segments to the path
            for coord in coords[1:]:
                path.push(f'L {coord[0]},{coord[1]}')
                path.push('Z')
            group.add(path)

        if isinstance(polygon, MultiPolygon):
            for poly in polygon.geoms:
                coords = [(coord[0], max_y - coord[1]) for coord in poly.exterior.coords]

                # Create a path
                path = dwg.path(d=f'M {coords[0][0]},{coords[0][1]}')

                # Add line segments to the path
                for coord in coords[1:]:
                    path.push(f'L {coord[0]},{coord[1]}')
                    path.push('Z')
                group.add(path)

    # Add the group to the drawing
    dwg.add(group)

    # Save the drawing
    dwg.save()


def simple_svg_save(polygon_list, filename='tramo7.2.svg', size=('1800mm', '2100mm'), label=True):
    # Create a new SVG drawing with 1mm = 1 user unit scale
    dwg = svgwrite.Drawing(filename, size=size, profile='full', viewBox=f"0 0 {size[0].replace('mm','')} {size[1].replace('mm','')}")
    
    # Create a group for all paths & add transform to center the group
    hat_group = dwg.g(fill='none', stroke='blue', 
                  stroke_width=0.1, 
                  )
    hole_group = dwg.g(fill='none', stroke='red', 
                  stroke_width=0.5, 
                  )
    
    for polygon in polygon_list:
        if isinstance(polygon, Polygon):
            coords = [(coord[0], - coord[1]) for coord in polygon.exterior.coords]
            path = dwg.path(d=f'M {coords[0][0]},{coords[0][1]}')
            for coord in coords[1:]:
                path.push(f'L {coord[0]},{coord[1]}')
            path.push('Z')
            hat_group.add(path)
            # Find the index of the polygon in the list
            try:
                idx = polygon_list.index(polygon)
            except ValueError:
                idx = None
            if idx is not None and label==True:
                # Compute the centroid
                centroid_pt = polygon.centroid
                # svgwrite uses (x, y) positions
                hat_group.add(
                    dwg.text(
                        str(int(idx / 2)),
                        insert=(centroid_pt.x, centroid_pt.y),
                        text_anchor="middle",
                        alignment_baseline="middle",
                        font_size="14px",
                        fill="black"
                    )
                )
        if isinstance(polygon, MultiPolygon):
            for poly in polygon.geoms:
                coords = [(coord[0], -coord[1]) for coord in poly.exterior.coords]
                path = dwg.path(d=f'M {coords[0][0]},{coords[0][1]}')
                for coord in coords[1:]:
                    path.push(f'L {coord[0]},{coord[1]}')
                path.push('Z')
                hole_group.add(path)
    dwg.add(hat_group)
    dwg.add(hole_group)
    dwg.save()
    
    return dwg

def add_tile(tile_width, tile_height, polygon_list, center_tile=False,up_shift=0):
    # create tile, center it on the polygons
    tile = shp_polys([[0,0], [tile_width, 0],
                  [tile_width, tile_height], [0, tile_height]]) 
    
    if center_tile:
        # calculate horizontal span /middle of polygons
        left_most_polygon = min(polygon_list, key=lambda x: x.bounds[0])
        right_most_polygon = max(polygon_list, key=lambda x: x.bounds[2])
        
        middle_of_polygons = (left_most_polygon.bounds[0] + right_most_polygon.bounds[2])/2
        middle_of_tile = (tile.bounds[0] + tile.bounds[2])/2
        shift_to_edge =  left_most_polygon.bounds[0] - tile.bounds[0] 
        tile = affinity.translate(tile, shift_to_edge, up_shift)
        
        middle_of_tile = (tile.bounds[0] + tile.bounds[2])/2
        shift_to_middle = middle_of_polygons - middle_of_tile
        print(shift_to_edge,shift_to_middle)
        tile = affinity.translate(tile, shift_to_middle, 0)
        
    return tile

def add_inner_tile(outer_tile, endtile=False):
    if endtile:
        TILE_BOTTOM_MARGIN = 30
        INNER_TILE_HEIGHT = 148
    else:
        TILE_BOTTOM_MARGIN = 26
        INNER_TILE_HEIGHT = 122
    
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

def crop_and_save_tile(polygons, inner_tile, save_holes=True):
    cropped_polygons = []
    
    # keep only the holes
    if save_holes:
        # keep only holes
        polygons = [poly for poly in polygons if poly.geom_type == 'MultiPolygon']
    else:
        # keep all (multi and single) polygons
        polygons = _flatten_polygons(_ensure_iterable(polygons))
    
    print(len(polygons))
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
    return cropped_polygons