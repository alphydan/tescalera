"""
Generate a "P2" Penrose tiling - an aperiodic tiling composed
of "kite" and "dart" shapes.
script by [tangentstorm](http://tangentstorm.com/)
"""
import math
import argparse

from shapely.geometry import Polygon

PHI = (1 + math.sqrt(5)) / 2

# The kite and dart each have a "pointy end" with a 72-degree angle.
# Imagine laying the tile on its side so that one side of this corner is
# a horizontal line, and the corner is pointing to the left. The vertex
# at this corner is our starting point. We now model the shape as a
# sequence of (angle, distance) pairs taking us clockwise around the shape.
KITE = [(72, PHI), (72, 1), (144, 1), (72, PHI)]
DART = [(72, PHI), (36, 1), (216, 1), (36, PHI)]


class Vec2:
    """A 2d vector, or point on a 2d plane"""

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        """convert to string, for (e.g.) print()"""
        return "(%0.3f, %0.3f)" % (self.x, self.y)

    def __sub__(self, other):
        """element-wise subtraction of two vectors"""
        return Vec2(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        """element-wise addition of two vectors"""
        return Vec2(self.x + other.x, self.y + other.y)

    def __mul__(self, other):
        """scale this vector by an amount"""
        if isinstance(other, float):
            return Vec2(self.x * other, self.y * other)
        elif isinstance(other, int):
            return self * float(other)
        else:
            raise NotImplementedError()

    def __hash__(self):
        # convert to string so the hash isn't effected by small floating point errors
        return hash(str(self))

    def __eq__(self, other):
        epsilon = 1e-6
        return abs(self.x - other.x) < epsilon and abs(self.y - other.y) < epsilon

    def offset(self, angle, distance):
        """
        Calculate a new point given an angle and distance.
        The angle is in degrees, with 0 pointing to
        the right, and 90 pointing upward
        """
        rad = math.radians(angle)
        x = self.x + distance * math.cos(rad)
        y = self.y + distance * math.sin(rad)
        return Vec2(x, y)

    def dot(self, other):
        """return the 'dot product' with other vector"""
        return self.x * other.x + self.y * other.y

    def dist(self, other):
        """returns a scalar representing the distance to the other point"""
        return math.sqrt((other.x - self.x) ** 2 + (other.y - self.y) ** 2)

    def length(self):
        """magnitude of the vector / the distance from the origin"""
        return self.dist(Vec2.ZERO)

    def norm(self):
        """normalize this vector to length=1"""
        length = self.length()
        return Vec2(self.x / length, self.y / length) if length > 0 else Vec2.ZERO


Vec2.ZERO = Vec2(0, 0)


class Tile:
    """
    Represents an arbitrary tile (polygon) anchored at a
    given location and "pointing" in a given direction.
    """

    def __init__(self, shape, location, heading, scale):
        """
        shape = a list of points that serve as a "template"
          (in this case, generally a reference to KITE or DART)
        location = a Vec2 locating an arbitrary point on the shape.
          (for the penrose tiles, it's the "pointy" end of the shape)
        heading = angle we're facing (0=right, 90=up)
        scale = scaling factor (length of the "short" sides)
        """
        self.shape = shape
        self.location = location
        self.heading = heading
        self.scale = scale

    def __hash__(self):
        return hash((id(self.shape), self.location, self.heading, self.scale))

    def __eq__(self, other):
        for slot in ['shape', 'location', 'heading', 'scale']:
            if getattr(self, slot) != getattr(other, slot):
                return False
        return True

    def translate(self, dxy):
        return Tile(self.shape, self.location + dxy, self.heading, self.scale)

    def points(self):
        """generate the (scaled and rotated) points of the tile"""
        heading = self.heading
        point = self.location
        yield point
        for (angle, distance) in self.shape:
            heading = (heading + (180 - angle)) % 360
            other = point.offset(heading, distance * self.scale)
            point = other
            yield point

    def lines(self):
        """generate the lines of this shape as (x1,y1,x2,y2) tuples"""
        points = self.points()
        point = start = next(points)
        for other in points:
            yield point.x, point.y, other.x, other.y
            point = other
        yield point.x, point.y, start.x, start.y

    def centroid(self):
        """
        Calculate the centroid of the tile.
        (Generic algorithm for any polygon)
        """
        points = list(self.points())
        n = len(points)
        area = 0
        cx = 0
        cy = 0

        for i in range(n):
            j = (i + 1) % n
            cross_product = points[i].x * points[j].y - points[j].x * points[i].y
            area += cross_product
            cx += (points[i].x + points[j].x) * cross_product
            cy += (points[i].y + points[j].y) * cross_product

        area /= 2
        cx /= (6 * area)
        cy /= (6 * area)

        return Vec2(cx, cy)

    def scale_by(self, factor):
        """
        To scale one of these tiles, imagine a line segment from the
        centroid of the tile to one of the corners. Scale this line
        and redraw the shape according to the new scale.
        """
        c = self.centroid()
        p = c + (self.location - c) * factor
        return self.__class__(self.shape, p, self.heading, self.scale * factor)

    def inflate(self):
        """
        To generate a tiling, we can replace each kite with two smaller kites and two
        darts, and each dart with two smaller darts and a kite.
        """
        p = list(self.points())
        h = self.heading
        s = self.scale / PHI

        def aa(a0, a1):
            return (a0 + a1) % 360  # add two angles

        def an(n):
            return (self.heading + sum([a for (a, _) in self.shape[:n]])) % 360  # (angle of point n)

        if self.shape == KITE:
            res = [dart(p[0], aa(h, -36), s),
                   dart(p[0], aa(h, +36), s),
                   kite(p[1], aa(an(1), +36), s),
                   kite(p[3], aa(an(3), -36), s)]
        elif self.shape == DART:
            res = [kite(p[0], h, s), dart(p[1], aa(an(1), 72), s), dart(p[3], aa(an(3), -108), s)]
        else:
            raise NotImplementedError("Can only inflate kites and darts")
        return res

    def svg(self):
        """
        Generate an SVG representation of the tile.
        """
        p = ' '.join(str(p)[1:-1] for p in self.points())
        # c = 'kite' if self.shape == KITE else 'dart'
        s = 'fill:none;stroke:#0000ff;stroke-width:0.01;stroke-linecap:round;'
        s += 'stroke-dasharray:none;stroke-opacity:1;-inkscape-stroke:hairline'
        return '<polygon style="%s" points="%s"/>' % (s, p)
    
    def coords(self):
        """
        Return the coordinates of the tile as a list of (x, y) tuples.
        """
        return [(p.x, p.y) for p in self.points()]

def dart(p, h, s):
    return Tile(DART, p, heading=h, scale=s)


def kite(p, h, s):
    return Tile(KITE, p, heading=h, scale=s)


# scale factor for tiles
SCALE_FACTOR = 600  
# five kites coming together at a point make a "sun", five kites a "star"
SUN = set([kite(Vec2.ZERO, h=72 * i, s=SCALE_FACTOR) for i in range(5)])
STAR = set([dart(Vec2.ZERO, h=72 * i, s=SCALE_FACTOR) for i in range(5)])


def inflate(tiles):
    """
    Perform the "inflate" operation on a set of tiles.
    This operation replaces each tile with a set of smaller tiles.

    (In the literature, this is followed by scaling the whole drawing
    by PHI, but we ignore this since we're dealing with SVG).
    """
    res = set()
    for tile in tiles:
        for child in tile.inflate():
            res.add(child)
    return res


def iterate(initial_tiles, iters):
    """
    run the `inflate()` operation `iters` times.
    `initial_tiles` should be a list of tiles like SUN or STAR
    (or make your own)
    """
    tiles = initial_tiles
    for i in range(iters):
        tiles = inflate(tiles)
    return tiles


def build_svg(tiles):
    buf = []
    w = buf.append
    w('<svg version="1.1" width="2000" height="1200" xmlns="http://www.w3.org/2000/svg">')
    for tile in tiles:
        w(tile.svg())
    w('</svg>')
    return '\n'.join(buf)


def main(seed, iters):
    tiles = STAR if seed == "star" else SUN
    tiles = [t.translate(Vec2(800, 500)) for t in tiles]
    tiles = iterate(tiles, iters)
    svg = build_svg(tiles)
    path = "tiling-%s-%d.svg" % (seed, iters)
    with open(path,  "w") as out:
        out.write(svg)
    print("wrote %s tiles to %s" % (len(tiles), path))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default="sun", choices=["star", "sun"])
    parser.add_argument("--iters", default=4, type=int)
    return vars(parser.parse_args())



def get_shapely_polygons(tiles):
    """
    Convert a list of tiles to a list of Shapely polygons.
    """
    polygons = []
    for tile in tiles:
        polygons.append(Polygon(tile.coords()))
    return polygons
    
if __name__ == "__main__":
    main(**parse_args())
