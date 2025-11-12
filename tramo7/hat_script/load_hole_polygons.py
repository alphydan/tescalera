from xml.etree import ElementTree as ET
from svgpathtools import parse_path
from svgpathtools.parser import parse_transform
from svgpathtools.path import Line, CubicBezier

import os


def extract_points_from_path(path_data):
    """
    returns a list of points
    from the svg.path object
    """
    # keep only points that are Line or Bezier
    points = [(p.start.real, p.start.imag) 
              for p in path_data 
              if isinstance(p, (Line, CubicBezier))]
    # append the last point          
    points.append((path_data[-1].end.real, path_data[-1].end.imag))
    
    return points


def get_hole_points(svg_file_path=None):
    """
    Load hole polygons from an SVG file and return them as a list of points.
    
    Args:
        svg_file_path: Optional path to the SVG file. If None, uses 'hat_and_holes.svg'
                       in the same directory as this script.
    
    Returns:
        A list of tuples, where each tuple contains:
        - A list of (x, y) coordinate tuples representing the hole points
        - A transform object (or None) for the hole
    """
    if svg_file_path is None:
        svg_file_path = os.path.join(os.path.dirname(__file__), 'hat_and_holes.svg')
    
    tree = ET.parse(svg_file_path)
    root = tree.getroot()

    # Let's store the paths defining the holes
    hole_paths = []
    for path in root.iter('{http://www.w3.org/2000/svg}path'):
        if 'hole' in path.get('id'):
            path_data = parse_path(path.get('d'))
            hole_paths.append(path_data)

    hole_points = []
    # create list of holes with sub-lists of tuples (points)
    for hole in hole_paths:
        hole_points.append(extract_points_from_path(hole))
    
    return hole_points


if __name__ == "__main__":
    # Allow running as a script for testing
    hole_points = get_hole_points()
    print(hole_points)