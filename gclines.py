import csv
import logging
import math

import geojson
from geographiclib.geodesic import Geodesic
from geojson import Feature, FeatureCollection, LineString, Point

logging.basicConfig()
logger = logging.getLogger("create_route_points")
logger.setLevel(logging.INFO)


def determine_route_direction(geodesic):
    g = geodesic.ArcPosition(1, Geodesic.LATITUDE | Geodesic.LONGITUDE)
    return "west" if g["azi1"] < 0 else "east"


def check_longitude_value_for_split(route, lon, direction, split_lon, prev_lon):
    if direction == "east":
        if lon > split_lon or (lon * prev_lon < 0 and abs(lon) + abs(prev_lon) > 350):
            return route + "_1", False
        else:
            return route, True
    elif direction == "west":
        split_lon = split_lon if split_lon != 180 else -180
        if lon < split_lon or (lon * prev_lon < 0 and abs(lon) + abs(prev_lon) > 350):
            return route + "_1", False
        else:
            return route, True
    else:
        raise ValueError(f"Unexpected direction: {direction}")


def make_coord_pair(csv_row):
    return (float(csv_row["longitude"]), float(csv_row["latitude"]))


def create_airport_dict():
    airports = dict()
    with open("airports.csv", encoding="utf8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["iata_code"] != "":
                attributes = {
                    "name": row["name"],
                    "loc_name": row["municipality"],
                    "lat": row["latitude_deg"],
                    "lon": row["longitude_deg"],
                }
                airports[row["iata_code"]] = attributes
    return airports


def output_airport_points(airport_dict: dict):
    airport_list = list()
    routes = dict()
    with open("routes.csv", encoding="utf8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                airport_from = row["from"]
                airport_to = row["to"]
                routes[airport_from + "-" + airport_to] = {
                    "from_lat": float(airport_dict[airport_from]["lat"]),
                    "from_lon": float(airport_dict[airport_from]["lon"]),
                    "to_lat": float(airport_dict[airport_to]["lat"]),
                    "to_lon": float(airport_dict[airport_to]["lon"]),
                }
                airport_list.append(airport_from)
                airport_list.append(airport_to)
            except KeyError:
                logger.warning(
                    f"Could not process route {airport_from} to {airport_to}"
                )

    with open("airport_points.csv", mode="w", encoding="utf8", newline="") as csv_file:
        fieldnames = ["iata_code", "name", "loc_name", "latitude", "longitude"]
        writer = csv.writer(csv_file)
        writer.writerow(fieldnames)
        for airport in sorted(set(airport_list)):
            writer.writerow([airport] + list(airport_dict[airport].values()))

    return routes


def create_route_points(split_longitude=180, create_geojson=True):
    airports = create_airport_dict()
    routes = output_airport_points(airport_dict=airports)

    with open("route_points.csv", mode="w", encoding="utf8", newline="") as csv_file:
        fieldnames = ["route", "latitude", "longitude"]
        writer = csv.writer(csv_file)
        writer.writerow(fieldnames)

        for route in routes:
            logger.info(f"Calculating {route}")
            # https://geographiclib.sourceforge.io/Python/doc/examples.html#computing-waypoints
            geod = Geodesic.WGS84
            item = routes[route]
            logger.debug(item)
            geod_line = geod.InverseLine(
                item["from_lat"],
                item["from_lon"],
                item["to_lat"],
                item["to_lon"],
                Geodesic.LATITUDE | Geodesic.LONGITUDE,
            )
            da = 1
            n = int(math.ceil(geod_line.a13 / da))
            da = geod_line.a13 / n
            direction = determine_route_direction(geod_line)
            logger.debug(direction)
            check_for_split = True
            prev_lon = item["from_lon"]
            for i in range(n + 1):
                a = da * i
                g = geod_line.ArcPosition(a, Geodesic.LATITUDE | Geodesic.LONGITUDE)
                if check_for_split:
                    route, check_for_split = check_longitude_value_for_split(
                        route, g["lon2"], direction, split_longitude, prev_lon
                    )
                writer.writerow(
                    [route, "{:.5f}".format(g["lat2"]), "{:.5f}".format(g["lon2"])]
                )
                prev_lon = g["lon2"]

    if create_geojson:
        # Routes
        routes_list = {}
        with open("route_points.csv", mode="r") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=",")
            for row in reader:
                if row["route"] in routes_list:
                    routes_list[row["route"]].append(make_coord_pair(row))
                else:
                    routes_list[row["route"]] = [make_coord_pair(row)]

        route_features_list = []
        for route in routes_list:
            route_features_list.append(
                Feature(
                    geometry=LineString(routes_list[route]), properties={"route": route}
                )
            )

        route_feature_collection = FeatureCollection(route_features_list)
        with open("route_lines.geojson", "w") as f:
            geojson.dump(route_feature_collection, f, indent=4)

        # Airports
        airport_features_list = []
        with open("airport_points.csv", mode="r") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=",")
            for row in reader:
                airport_features_list.append(
                    Feature(
                        geometry=Point(make_coord_pair(row)),
                        properties={
                            "name": f"{row['iata_code']} {row['loc_name']}",
                            "iata_code": row["iata_code"],
                            "airport_name": row["name"],
                            "loc_name": row["loc_name"],
                        },
                    )
                )

        airport_feature_collection = FeatureCollection(airport_features_list)
        with open("airport_points.geojson", "w") as f:
            geojson.dump(airport_feature_collection, f, indent=4)


if __name__ == "__main__":
    create_route_points()
