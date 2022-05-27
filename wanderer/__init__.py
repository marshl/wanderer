import json
import json
import os
import re
from typing import List, Tuple

from PIL import Image
from PIL.ImageDraw import ImageDraw

from wanderer.game import Game, MovementType, GameMap, MapMarker
from wanderer.position2d import Position2D


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

