import math
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, box
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

# Plot polygon list
def plot_polygon_list(polygons, colors=None, alphas=None):
    fig, ax = plt.subplots(figsize=(5, 5))

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

    for polygon  in polygons:
        x, y = polygon.exterior.xy
        ax.plot(x, y, color='blue', linewidth=0.5)

    ax.axis('equal')
    plt.show()




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


def save_polygon_list_to_svg(polygon_list, filename='tramo1.2.svg', size=('1200mm', '300mm')):
    # Create a new SVG drawing with 1mm = 1 user unit scale
    dwg = svgwrite.Drawing(filename, size=size, profile='full', viewBox=f"0 0 {size[0].replace('mm','')} {size[1].replace('mm','')}")
    
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

