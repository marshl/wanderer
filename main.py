import dataclasses
import os
import re
from typing import List, Dict, Tuple

from PIL import Image
from PIL.ImageDraw import ImageDraw


def render_thingy(map_type, route_name):
    map_directory = os.path.join("maps", map_type)
    if not os.path.exists(map_directory):
        raise ValueError(f"Cannot find map {map_directory}")

    map_file = os.path.join(map_directory, "MojaveMapBW.png")
    if not os.path.exists(map_directory):
        raise ValueError(f"Cannot find map {map_file}")

    route_file = os.path.join(map_directory, "routes", f"{route_name}.txt")
    if not os.path.exists(route_file):
        raise ValueError(f"Cannot find route {route_file}")

    output_directory = os.path.join(map_directory, "output")
    if not os.path.isdir(output_directory):
        raise ValueError(f"Cannot find output directory {output_directory}")

    location_file = os.path.join(map_directory, "locations.txt")
    locations = parse_location_file(location_file)

    movements = parse_route_file(route_file, locations)

    with Image.open(map_file) as im:
        draw = ImageDraw(im)
        # draw.line((0, 0) + im.size, fill=128)
        # draw.line((0, im.size[1], im.size[0], 0), fill=128)
        for movement in movements:
            draw.line(
                (movement.start.x, movement.start.y, movement.end.x, movement.end.y),
                fill=(255,0,0),
            )

        output_file = os.path.join(output_directory, "output.jpeg")
        im.save(output_file, "jpeg")


@dataclasses.dataclass
class Location:
    x: int
    y: int
    name: str


def parse_location_file(location_path: str) -> Dict[str, Location]:
    if not os.path.isfile(location_path):
        raise ValueError(f'Cannot find location file "{location_path}"')

    locations: Dict[str, Location] = {}
    with open(location_path, "r") as location_file:
        for line in location_file.readlines():
            line = line.strip()
            if not line:
                continue
            location = parse_location(line)
            if location.name in locations:
                raise ValueError(f"Location {location.name} already in locations list")
            locations[location.name] = location
    return locations


@dataclasses.dataclass
class Movement:
    start: Location
    end: Location
    movement_type: str


def parse_route_file(filename: str, locations: Dict[str, Location]):
    if not os.path.isfile(filename):
        raise ValueError(f'Cannot find route file "{filename}"')
    with open(filename, "r") as route_file:
        lines = route_file.readlines()

    start_match = re.match("^start in (?P<location>.+)$", lines[0].strip())
    start_location = locations.get(start_match.group("location"))
    if not start_location:
        raise ValueError(
            f"Unknown starting location \"{start_match.group('location')}\""
        )

    movements: List[Movement] = []
    last_location = start_location
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        movement, location = parse_route_str(line)
        if location not in locations:
            raise ValueError(f"Unknown location {location}")
        movements.append(
            Movement(
                start=last_location, end=locations[location], movement_type=movement
            )
        )
    return movements


def parse_route_str(route_str: str) -> Tuple[str, str]:
    match = re.match("^(?P<movement>.+?) to (?P<location>.+?)$", route_str)
    if not match:
        raise ValueError(f'Could not match line to route: "{route_str}"')
    return match.group("movement"), match.group("location")


def parse_location(location_str: str):
    match = re.match("^(?P<name>.+?) (?P<x>[0-9]+)x +(?P<y>[0-9]+)y *$", location_str)
    x = int(match.group("x"))
    y = int(match.group("y"))
    name = match.group("name")
    return Location(x=x, y=y, name=name)


if __name__ == "__main__":
    render_thingy("new_vegas", "survival")
