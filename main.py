import dataclasses
import json
import os
import re
from typing import List, Dict, Tuple
import math

from PIL import Image
from PIL.ImageDraw import ImageDraw


@dataclasses.dataclass
class Position2D:
    """
    A position in 2D space
    """

    x: float  # pylint: disable=invalid-name
    y: float  # pylint: disable=invalid-name

    def __hash__(self):
        return hash((self.x, self.y))

    def __sub__(self, other: "Position2D") -> "Position2D":
        """
        Subtracts the other vector from this one and returns the result
        :param other: The other position
        :return: A new vector of z where z = this-other
        >>> Position2D(x=10, y=5) - Position2D(x=3, y=2)
        Position2D(x=7, y=3)
        """
        return Position2D(x=self.x - other.x, y=self.y - other.y)

    def __add__(self, other: "Position2D") -> "Position2D":
        """
        Adds this vector to the other vector
        :param other: The other vector to add to
        :return: A new vector of the two combined
        """
        return Position2D(x=self.x + other.x, y=self.y + other.y)

    def __truediv__(self, other: float) -> "Position2D":
        """
        Gets this vector divided by a scalar value
        :param other: The scalar value to divide by
        :return: A new vector.
        """
        return Position2D(x=self.x / other, y=self.y / other)

    def dot_product(self, other: "Position2D") -> float:
        """
        Gets the dot product of this vector to the other vector
        :param other: The other vector
        :return: The dot product of the two vectors
        """
        return self.x * other.x + self.y * other.y

    def cross_product_scalar(self, other: "Position2D") -> float:
        """

        :param other:
        :return:
        >>> Position2D(x=5, y=0).cross_product_scalar(Position2D(x=0, y=4))
        1.0
        >>> Position2D(x=0, y=3).cross_product_scalar(Position2D(x=4, y=0))
        -1.0
        """
        return (self.x * other.y - self.y * other.x) / (
            self.magnitude() * other.magnitude()
        )

    def magnitude(self) -> float:
        """
        Gets the magnitude of this vector
        :return: The magnitude of this vector
        """
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def angle_between(self, other: "Position2D") -> float:
        """
        Gets the angle between this vector and the other vector
        :param other: The other vector to get the angle between
        :return:
        >>> Position2D(x=0.5, y=0.5).angle_between(Position2D(x=0, y=1))
        0.7853981633974484
        """
        total_magnitude = self.magnitude() * other.magnitude()
        if total_magnitude == 0:
            return 0
        try:
            return math.acos(self.dot_product(other) / total_magnitude)
        except ValueError:
            return 0


class Game:
    def __init__(self, name: str, default_map: str):
        self.name = name
        self.default_map = default_map
        self.movement_types: List[MovementType] = []

    def __str__(self):
        return self.name


class GameMap:
    def __init__(self, game: Game, name: str, image_file: str, speed_multiplier: float):
        assert speed_multiplier > 0
        self.game: Game = game
        self.name: str = name
        self.image_file: str = image_file
        self.speed_multiplier: float = speed_multiplier
        self.locations = []

    def __str__(self):
        return self.name


class MapMarker:
    def __init__(self, name: str, game_map: GameMap, position: Position2D):
        self.name = name
        self.game_map = game_map
        self.position = position

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
        for idx, movement in enumerate(movements):
            draw.line(
                (movement.start.x, movement.start.y, movement.end.x, movement.end.y),
                fill=(255, 0, 0),
            )

            output_file = os.path.join(output_directory, f"output_{idx}.jpeg")
            im.save(output_file, "jpeg")


# def parse_location_file(location_path: str) -> Dict[str, Location]:
#     if not os.path.isfile(location_path):
#         raise ValueError(f'Cannot find location file "{location_path}"')
#
#     locations: Dict[str, Location] = {}
#     with open(location_path, "r") as location_file:
#         for line in location_file.readlines():
#             line = line.strip()
#             if not line:
#                 continue
#             location = parse_location(line)
#             if location.name in locations:
#                 raise ValueError(f"Location {location.name} already in locations list")
#             locations[location.name] = location
#     return locations

#
# def parse_route_file(filename: str, locations: Dict[str, Location]):
#     if not os.path.isfile(filename):
#         raise ValueError(f'Cannot find route file "{filename}"')
#     with open(filename, "r") as route_file:
#         lines = route_file.readlines()
#
#     start_match = re.match("^start in (?P<location>.+)$", lines[0].strip())
#     start_location = locations.get(start_match.group("location"))
#     if not start_location:
#         raise ValueError(
#             f"Unknown starting location \"{start_match.group('location')}\""
#         )
#
#     movements: List[Movement] = []
#     last_location = start_location
#     for line in lines[1:]:
#         line = line.strip()
#         if not line:
#             continue
#         movement, location = parse_route_str(line)
#         if location not in locations:
#             raise ValueError(f"Unknown location {location}")
#         movements.append(
#             Movement(
#                 start=last_location, end=locations[location], movement_type=movement
#             )
#         )
#     return movements


def parse_route_str(route_str: str) -> Tuple[str, str]:
    match = re.match("^(?P<movement>.+?) to (?P<location>.+?)$", route_str)
    if not match:
        raise ValueError(f'Could not match line to route: "{route_str}"')
    return match.group("movement"), match.group("location")


# def parse_location(location_str: str):
#     match = re.match("^(?P<name>.+?) (?P<x>[0-9]+)x +(?P<y>[0-9]+)y *$", location_str)
#     x = int(match.group("x"))
#     y = int(match.group("y"))
#     name = match.group("name")
#     return Location(x=x, y=y, name=name)


GAMES_DIRECTORY = "games"


def get_games_folder():
    return os.path.abspath(GAMES_DIRECTORY)


def get_available_games() -> List[str]:
    games_folder = get_games_folder()
    if not os.path.exists(games_folder):
        raise ValueError(f'Cannot find "{games_folder}" directory')
    folder_names = [
        filename
        for filename in os.listdir(games_folder)
        if os.path.isdir(os.path.join(games_folder, filename))
    ]
    if not folder_names:
        raise ValueError(f"No games found in {games_folder}")
    return folder_names


def parse_game(game_name: str) -> Game:
    available_games = get_available_games()
    if game_name not in available_games:
        raise ValueError(
            f'Cannot find game "{game_name}". Available games are {available_games}'
        )

    game_folder = os.path.join(get_games_folder(), game_name)
    if not os.path.exists(game_folder) or not os.path.isdir(game_folder):
        raise ValueError(f"Game folder {game_folder} could not be found")

    config_filename = os.path.join(game_folder, "config.json")
    with open(config_filename, "r", encoding="utf8") as file:
        game_config = json.load(file)
    game = Game(name=game_config["name"], default_map=game_config["default_map"])

    movement_types = [
        MovementType(
            name=movement_type["name"],
            pixels_per_second=movement_type["pixels_per_second"],
            colour_code=movement_type["colour"],
        )
        for movement_type in game_config["movement_types"]
    ]
    game.movement_types = movement_types

    root_map_directory = os.path.join(game_folder, "maps")
    if not os.path.exists(root_map_directory) or not os.path.isdir(root_map_directory):
        raise ValueError(
            f"Map directory {root_map_directory} could not be found or is not a directory."
        )
    child_map_directories = [
        child_map_dir
        for child_map_dir in [
            os.path.join(root_map_directory, filename)
            for filename in os.listdir(root_map_directory)
        ]
        if os.path.isdir(child_map_dir)
    ]

    if not child_map_directories:
        raise ValueError(f"Map directory {root_map_directory} has no subfolders in it")

    # for map_directory in child_map_directories:
    game.maps = [
        parse_game_map(map_directory, game) for map_directory in child_map_directories
    ]

    return game


def parse_location(location_config: dict, game_map: GameMap) -> MapMarker:
    return MapMarker(
        name=location_config["name"],
        game_map=game_map,
        position=Position2D(x=location_config["x"], y=location_config["y"]),
    )


def parse_game_map(map_directory: str, game: Game):
    config_filename = "config.json"
    config_filepath = os.path.join(map_directory, config_filename)
    if not os.path.exists(config_filepath):
        raise ValueError(f"Could not find {config_filename} file in {map_directory}")

    with open(config_filepath, "r", encoding="utf8") as file:
        map_config = json.load(file)

    game_map = GameMap(
        game=game,
        name=map_config["name"],
        image_file=os.path.join(map_directory, map_config["image_file"]),
        speed_multiplier=map_config["speed_multiplier"],
    )
    game_map.locations = [
        parse_location(location_config=location_config, game_map=game_map)
        for location_config in map_config["locations"]
    ]
    return game_map


if __name__ == "__main__":
    # render_thingy("new_vegas", "survival")
    parse_game("new_vegas")
