import json
import os
import re
from typing import List, Dict, Tuple

from PIL import Image
from rapidfuzz import fuzz
from slugify import slugify

from wanderer.position2d import Position2D


GAMES_DIRECTORY = "games"


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

    def colour_tuple(self) -> Tuple[int, int, int, int]:
        colour_int = int(self.colour_code, 0)
        r = (colour_int & int("0xff000000", 0)) >> 24
        g = (colour_int & int("0x00ff0000", 0)) >> 16
        b = (colour_int & int("0x0000ff00", 0)) >> 8
        a = colour_int & int("0x000000ff", 0)
        return r, g, b, a


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
            locations += game_map.find_location_by_name(location_name, fuzzy=False)

        if len(locations) > 1:
            raise ValueError(f'Too many location match the name "{location_name}"')

        if len(locations) == 0:
            fuzzy_locations = []
            for game_map in self.game_maps:
                fuzzy_locations += game_map.find_location_by_name(
                    location_name, fuzzy=True
                )

            if fuzzy_locations:
                raise ValueError(
                    f'Cannot find location with name "{location_name}". '
                    f'Did you mean {" or ".join(loc.name for loc in fuzzy_locations)}?'
                )
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

    @classmethod
    def load_from_dict(cls, game_config: dict, game_folder: str) -> "Game":
        game = Game(
            path=game_folder,
            name=game_config["name"],
            default_map=game_config["default_map"],
        )

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

        game.game_maps = [
            parse_game_map(map_directory, game) for map_directory in child_map_directories
        ]

        return game


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
        name_slug = slugify(location.name)
        if name_slug in self.location_map:
            raise ValueError(
                f'Location "{location.name}" ({name_slug}) already exists in map {self}'
            )
        self.location_map[name_slug] = location

    def find_location_by_name(
        self, location_name: str, fuzzy: bool = False
    ) -> List["MapMarker"]:
        if not fuzzy:
            location = self.location_map.get(slugify(location_name))
            return [location] if location else []

        locations = [
            location
            for location in self.location_map.values()
            if fuzz.ratio(location_name, location.name) >= 55
        ]
        return locations

    def get_image_path(self) -> str:
        return os.path.join(self.game.path, self.image_file)

    def get_crop_at_position(
        self, position: Position2D, crop_size: Tuple[int, int]
    ) -> Tuple[int, int, int, int]:
        height, width = crop_size

        if width > self.image_size.x or height > self.image_size.y:
            raise ValueError(
                f"Crop {crop_size} is larger than source image {self.image_size}"
            )

        center_x = int(max(width / 2, min(position.x, self.image_size.x - width / 2)))
        center_y = int(max(height / 2, min(position.y, self.image_size.y - height / 2)))
        return (
            int(center_x - width / 2),
            int(center_y - height / 2),
            int(center_x + width / 2),
            int(center_y + height / 2),
        )

    @classmethod
    def load_from_config(cls, map_config: dict, map_directory: str, game: Game) -> "GameMap":
        game_map = GameMap(
            game=game,
            name=map_config["name"],
            image_file=os.path.join(map_directory, map_config["image_file"]),
            speed_multiplier=map_config["speed_multiplier"],
        )
        for location_config in map_config["locations"]:
            location = parse_location(location_config=location_config, game_map=game_map)
            game_map.add_location(location)
        return game_map


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
    return Game.load_from_dict(game_config, game_folder=game_folder)


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

    return GameMap.load_from_config(map_config, map_directory=map_directory, game=game)
