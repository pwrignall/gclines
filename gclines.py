import csv
from geographiclib.geodesic import Geodesic
import math
import logging

logging.basicConfig()
logger = logging.getLogger("create_route_points")
logger.setLevel(logging.INFO)


def determine_route_direction(geodesic):
    g = geodesic.ArcPosition(1, Geodesic.LATITUDE | Geodesic.LONGITUDE)
    return "west" if g["azi1"] < 0 else "east"


def check_longitude_value_for_split(route, lon, direction, split_lon):
    if direction == "east":
        if lon > split_lon:
            return route + "_1", False
        else:
            return route, True
    elif direction == "west":
        split_lon = split_lon if split_lon != 180 else -180
        if lon < split_lon:
            return route + "_1", False
        else:
            return route, True
    else:
        raise ValueError(f"Unexpected direction: {direction}")


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
            airport_from = row["from"]
            airport_to = row["to"]
            airport_list.append(airport_from)
            airport_list.append(airport_to)
            routes[airport_from + "-" + airport_to] = {
                "from_lat": float(airport_dict[airport_from]["lat"]),
                "from_lon": float(airport_dict[airport_from]["lon"]),
                "to_lat": float(airport_dict[airport_to]["lat"]),
                "to_lon": float(airport_dict[airport_to]["lon"]),
            }

    with open("airport_points.csv", mode="w", encoding="utf8", newline="") as csv_file:
        fieldnames = ["iata_code", "name", "loc_name", "latitude", "longitude"]
        writer = csv.writer(csv_file)
        writer.writerow(fieldnames)
        for airport in sorted(set(airport_list)):
            writer.writerow([airport] + list(airport_dict[airport].values()))

    return routes


def create_route_points(split_longitude=180):
    airports = create_airport_dict()
    routes = output_airport_points(airport_dict=airports)
    # https://geographiclib.sourceforge.io/Python/doc/examples.html#computing-waypoints
    geod = Geodesic.WGS84

    with open("route_points.csv", mode="w", encoding="utf8", newline="") as csv_file:
        fieldnames = ["route", "latitude", "longitude"]
        writer = csv.writer(csv_file)
        writer.writerow(fieldnames)

        for route in routes:
            logger.info(f"Calculating {route}")
            item = routes[route]
            logger.debug(item)
            l = geod.InverseLine(item["from_lat"], item["from_lon"], item["to_lat"], item["to_lon"],
                                 Geodesic.LATITUDE | Geodesic.LONGITUDE, )
            da = 1
            n = int(math.ceil(l.a13 / da))
            da = l.a13 / n
            direction = determine_route_direction(l)
            logger.debug(direction)
            check_for_split = True
            for i in range(n + 1):
                a = da * i
                g = l.ArcPosition(a, Geodesic.LATITUDE | Geodesic.LONGITUDE | Geodesic.LONG_UNROLL)
                if check_for_split:
                    route, check_for_split = check_longitude_value_for_split(route, g["lon2"], direction,
                                                                             split_longitude)
                writer.writerow([route, "{:.5f}".format(g["lat2"]), "{:.5f}".format(g["lon2"])])


if __name__ == "__main__":
    create_route_points()
