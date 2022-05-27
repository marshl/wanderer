import os
import re
from typing import List, Dict, Tuple

from PIL import Image
from PIL.ImageDraw import ImageDraw

from wanderer.position2d import Position2D


class MapMarker:
    def __init__(self, name: str, position: Position2D, game_map: "GameMap"):
        self.name = name
        self.position = position
        self.game_map = game_map

    def __str__(self):
        return self.name


class MovementType:
    def __init__(self, name: str, pixels_per_second: float, colour_code: str):
        assert pixels_per_second > 0
        self.name = name
        self.pixels_per_second = pixels_per_second
        self.colour_code = colour_code

    def __str__(self):
        return self.name


class Movement:
    def __init__(self, start: MapMarker, end: MapMarker, movement_type: MovementType):
        self.start = start
        self.end = end
        self.movement_type = movement_type

    def __str__(self):
        return f"{self.movement_type} from {self.start} to {self.end}"


class Game:
    def __init__(self, path: str, name: str, default_map: str):
        self.path = path
        self.name = name
        self.default_map = default_map
        self.movement_types: List[MovementType] = []
        self.game_maps: List[GameMap] = []

    def __str__(self):
        return self.name

    def find_location_by_name(self, location_name: str) -> "MapMarker":
        locations = []
        for game_map in self.game_maps:
            location = game_map.find_location_by_name(location_name)
            if location is not None:
                locations.append(location)

        if len(locations) > 1:
            raise ValueError(f'Too many location match the name "{location_name}"')

        if len(locations) == 0:
            raise ValueError(f'Cannot find location with name "{location_name}"')

        return locations[0]

    def parse_route_file(self, route_name: str) -> List[Movement]:
        routes = self.get_available_routes()
        if route_name not in routes:
            raise ValueError(f'Unknown route "{route_name}"')

        with open(
            os.path.join(os.path.join(self.path, "routes"), route_name),
            "r",
            encoding="utf8",
        ) as route_file:
            lines = route_file.readlines()

        start_match = re.match("^start in (?P<location>.+)$", lines[0].strip())
        location_name = start_match.group("location")
        start_location = self.find_location_by_name(location_name)

        movements: List[Movement] = []
        last_location = start_location
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            movement, location_name = self.parse_route_str(line)
            next_location = self.find_location_by_name(location_name)
            movement_type = self.get_movement_type(movement)
            movements.append(
                Movement(
                    start=last_location, end=next_location, movement_type=movement_type
                )
            )
            last_location = next_location
        return movements

    def get_movement_type(self, movement_type_name: str) -> MovementType:
        matching_types = [
            movement_type
            for movement_type in self.movement_types
            if movement_type.name.lower() == movement_type_name.lower()
        ]
        if len(matching_types) == 0:
            raise ValueError(f'Could not find movement type "{movement_type_name}"')

        if len(matching_types) > 1:
            raise ValueError(
                f'Too many matching movement types for "{movement_type_name}"'
            )
        return matching_types[0]

    def parse_route_str(self, route_str: str) -> Tuple[str, str]:
        match = re.match("^(?P<movement>.+?) to (?P<location>.+?)$", route_str)
        if not match:
            raise ValueError(f'Could not match line to route: "{route_str}"')
        return match.group("movement"), match.group("location")

    def get_available_routes(self):
        routes_dir = os.path.join(self.path, "routes")
        if not os.path.exists(routes_dir) or not os.path.isdir(routes_dir):
            raise ValueError(
                f"Could not find routes directory {routes_dir} for game {self}"
            )

        return [
            filename for filename in os.listdir(routes_dir) if filename.endswith(".txt")
        ]

    def render_route(self, route_name: str, output_directory: str):
        movements = self.parse_route_file(route_name)
        for idx, movement in enumerate(movements):
            assert movement.start.game_map == movement.end.game_map
            with Image.open(movement.start.game_map.get_image_path()) as im:
                draw = ImageDraw(im)
                print(movement)
                draw.line(
                    (
                        movement.start.position.x,
                        movement.start.position.y,
                        movement.end.position.x,
                        movement.end.position.y,
                    ),
                    fill=(255, 0, 0),
                )

                output_file = os.path.join(output_directory, f"output_{idx}.jpeg")
                im.save(output_file, "jpeg")
                # draw.line((0, 0) + im.size, fill=128)
                # draw.line((0, im.size[1], im.size[0], 0), fill=128)


class GameMap:
    def __init__(self, game: Game, name: str, image_file: str, speed_multiplier: float):
        assert speed_multiplier > 0
        self.game: Game = game
        self.name: str = name
        self.image_file: str = image_file
        self.speed_multiplier: float = speed_multiplier
        self.location_map: Dict[str, MapMarker] = {}

    def __str__(self):
        return self.name

    def add_location(self, location: "MapMarker") -> None:
        if location.name in self.location_map:
            raise ValueError(f'Location "{location.name}" already exists in map {self}')
        self.location_map[location.name] = location

    def find_location_by_name(self, location_name: str) -> "MapMarker":
        return self.location_map.get(location_name)

    def get_image_path(self) -> str:
        return os.path.join(self.game.path, self.image_file)
