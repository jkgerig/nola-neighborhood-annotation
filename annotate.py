#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import sys
import csv
import re
import fiona
import shapely.geometry
from shapely.geometry import Point

shp_file = "data/neighborhood_data/geo_export_d3ee4d7d-28a5-4a23-a6bb-c8f4747d5b62.shp"
fc = fiona.open(shp_file)

# A datastructure to hold a shape (neighborhood, beat, etc)
class Shape:
    def __init__(self, feature):
        self.polygon = shapely.geometry.shape(feature['geometry'])
        self.name = feature['properties']['gnocdc_lab']
        self.centroid = self.polygon.centroid

# convert to shapes
shapes = [Shape(feature) for feature in fc]

def sort_shapes(shapes, point):
    """
    Sorts the shapes by distance from the shape centroid to the given point
    """
    shapes.sort(key = lambda shape: shape.centroid.distance(point))
    return shapes

def find_neighborhood(lat, lng):
    """
    Finds the neighborhood given the lat, lng
    """
    point = Point(lng, lat)

    # sorts the shapes by distance from shape centroid the point
    sorted_shapes = sort_shapes(shapes, point)

    # now that shapes are sorted, we should find the
    # boundary shape pretty quick
    for shape in sorted_shapes:
        if shape.polygon.contains(point):
            return shape.name

    return None

lat_lng_rg = re.compile('.*?([+-]?\\d*\\.\\d+)(?![-+0-9\\.]).*?([+-]?\\d*\\.\\d+)(?![-+0-9\\.])')

def parse_lat_lng(lat_lng_string):
    """
    Turns the Location column into (lat, lng) floats
    May look like this "(29.98645605, -90.06910049)"
    May have degree symbol "(29.98645605°,-90.06910049°)"
    """
    m = lat_lng_rg.search(lat_lng_string)

    if m:
        return (float(m.group(1)), float(m.group(2)))
    else:
        return (None, None)

def annotate_csv(in_file, out_file):
    """
    Goes row by row through the in_file and
    writes out the row to the out_file with
    the new Neighbhorhood column
    """

    reader = csv.reader(in_file)
    writer = csv.writer(out_file)

    # Write headers first, add new neighborhood column
    headers = reader.next()
    headers.append('Neighborhood')

    writer.writerow(headers)

    for row in reader:
        # WGS84 point, "Location" column, is last element
        lat, lng = parse_lat_lng(row[-1])

        if lat and lng:
            neighborhood = find_neighborhood(lat, lng)
        else:
            neighborhood = 'N/A'

        row.append(neighborhood)
        writer.writerow(row)

        print "#%s lat: %s lng: %s -> %s" % (reader.line_num, lat, lng, neighborhood)

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print "Provide an output and an input csv file"
        print "Example: python annotate.py data/calls_for_service/2016.csv data/calls_for_service/2016_annotated.csv"
        sys.exit()

    in_file_path = sys.argv[1]
    out_file_path = sys.argv[2]

    with open(in_file_path, 'rb') as in_file:
        with open(out_file_path, 'wb') as out_file:
            annotate_csv(in_file, out_file)
