import math
import os
import re
import subprocess
from typing import Any, List, Dict, Tuple

from PIL import Image
from PIL.ImageDraw import ImageDraw

from wanderer.position2d import Position2D


def lerp(start: Any, end: Any, delta: float) -> Any:
    assert 0 <= delta <= 1.0

    return start + (end - start) * delta


def points_between(
    start: Position2D, end: Position2D, movement_speed: float
) -> List[Position2D]:
    assert movement_speed > 0
    if start == end:
        return [start]
    distance = (end - start).magnitude()

    moves = math.ceil(distance / movement_speed)

    points = [start + (end - start).unit() * i * movement_speed for i in range(moves)]
    return points


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
        index = 0
        for movement in movements:
            assert movement.start.game_map == movement.end.game_map
            index = self.render_movement(
                movement, current_index=index, output_directory=output_directory
            )

        subprocess.run(
            [
                "ffmpeg",
                "-framerate",
                "24",
                "-i",
                os.path.join(output_directory, "output_%05d.jpeg"),
                os.path.join(output_directory, "final.mp4"),
                "-y"
            ]
        )

    def render_movement(
        self, movement: Movement, current_index: int, output_directory: str
    ) -> int:
        movement_speed = (
            movement.movement_type.pixels_per_second
            * movement.start.game_map.speed_multiplier
        )
        points = points_between(
            movement.start.position, movement.end.position, movement_speed
        )
        with Image.open(movement.start.game_map.get_image_path()) as im:
            draw = ImageDraw(im)
            for point in points:
                draw.line(
                    (
                        movement.start.position.x,
                        movement.start.position.y,
                        point.x,
                        point.y,
                    ),
                    fill=(255, 0, 0),
                )

                output_file = os.path.join(
                    output_directory, self.get_output_filename(current_index)
                )
                current_index += 1
                crop = im.crop(
                    movement.start.game_map.get_crop_at_position(
                        point, Position2D(x=512, y=512)
                    )
                )
                crop.save(output_file, "jpeg")
        return current_index

    def get_output_filename(self, index: int):
        assert 0 <= index <= 10000
        return f"output_{index:05}.jpeg"


class GameMap:
    def __init__(self, game: Game, name: str, image_file: str, speed_multiplier: float):
        assert speed_multiplier > 0
        self.game: Game = game
        self.name: str = name
        self.image_file: str = image_file
        self.speed_multiplier: float = speed_multiplier
        self.location_map: Dict[str, MapMarker] = {}
        self.image = Image.open(self.image_file)
        self.image_size = Position2D(*self.image.size)

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

    def get_crop_at_position(
        self, position: Position2D, crop_size: Position2D
    ) -> Tuple[int, int, int, int]:
        if crop_size.x > self.image_size.x or crop_size.y > self.image_size.y:
            raise ValueError(
                f"Crop {crop_size} is larger than source image {self.image_size}"
            )
        center = position
        top_left = center - crop_size / 2
        if top_left.x < 0:
            top_left.x += top_left.x

        if top_left.y < 0:
            top_left.y += top_left.y

        bottom_right = center + crop_size / 2
        if bottom_right.x > self.image_size.x:
            bottom_right.x -= bottom_right.x - self.image_size.x
        if bottom_right.y > self.image_size.y:
            bottom_right.y -= bottom_right.y - self.image_size.y

        return (
            int(top_left.x),
            int(top_left.y),
            int(bottom_right.x),
            int(bottom_right.y),
        )