import numpy as np
from typing import List, Tuple, Set
from shapely.geometry import Polygon

def normalize_polygon(polygon) -> np.ndarray:
    """
    Normalize a polygon by rotating its points so that the first point
    is the one with minimum x (and minimum y in case of tie).
    This ensures that the same polygon with different starting points
    will be detected as duplicate.
    
    Args:
        polygon: Either a numpy array of shape (n, 2) or a Shapely Polygon object
    """
    # Convert Shapely Polygon to numpy array if needed
    if isinstance(polygon, Polygon):
        coords = np.array(polygon.exterior.coords)[:-1]  # Remove the repeated last point
    else:
        coords = polygon
    
    # Find the index of the leftmost point (minimum x)
    min_x = np.min(coords[:, 0])
    leftmost_indices = np.where(coords[:, 0] == min_x)[0]
    
    # If there are multiple points with the same x, take the one with minimum y
    if len(leftmost_indices) > 1:
        min_y = np.min(coords[leftmost_indices, 1])
        leftmost_index = leftmost_indices[np.where(coords[leftmost_indices, 1] == min_y)[0][0]]
    else:
        leftmost_index = leftmost_indices[0]
    
    # Roll the array so that the leftmost point is first
    return np.roll(coords, -leftmost_index, axis=0)

def find_duplicate_polygons(polygons: List, tolerance: float = 1e-10) -> List[Tuple[int, int]]:
    """
    Find duplicate polygons in a list of polygons.
    
    Args:
        polygons: List of numpy arrays or Shapely Polygon objects
        tolerance: Floating point tolerance for coordinate comparison
        
    Returns:
        List of tuples containing indices of duplicate polygons
    """
    duplicates = []
    seen_polygons: Set[str] = set()
    
    for i, poly in enumerate(polygons):
        # Normalize the polygon
        norm_poly = normalize_polygon(poly)
        
        # Convert to string representation for hashing
        # Round to handle floating point precision issues
        poly_str = str(np.round(norm_poly / tolerance) * tolerance)
        
        # Check if we've seen this polygon before
        if poly_str in seen_polygons:
            # Find the first occurrence of this polygon
            for j in range(i):
                norm_poly_j = normalize_polygon(polygons[j])
                poly_str_j = str(np.round(norm_poly_j / tolerance) * tolerance)
                if poly_str_j == poly_str:
                    duplicates.append((j, i))
                    break
        else:
            seen_polygons.add(poly_str)
    
    return duplicates

# Example usage
if __name__ == "__main__":
    # Example with both Shapely Polygons and numpy arrays
    # Using Shapely Polygons
    polygon1 = Polygon([[0, 0], [1, 0], [1, 1], [0, 1]])
    polygon2 = Polygon([[1, 0], [1, 1], [0, 1], [0, 0]])  # Same as polygon1 but different starting point
    polygon3 = Polygon([[2, 2], [3, 2], [3, 3], [2, 3]])  # Different polygon
    polygon4 = Polygon([[0, 0], [1, 0], [1, 1], [0, 1]])  # Duplicate of polygon1
    
    polygons = [polygon1, polygon2, polygon3, polygon4]
    
    # Find duplicates
    duplicates = find_duplicate_polygons(polygons)
    
    # Print results
    if duplicates:
        print("Found duplicate polygons at the following indices:")
        for i, j in duplicates:
            print(f"Polygon {i} and Polygon {j} are duplicates")
    else:
        print("No duplicate polygons found") 