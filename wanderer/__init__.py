import json
import os
from typing import List

from wanderer.game import Game, MovementType, GameMap, MapMarker
from wanderer.position2d import Position2D

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
    game = Game(path=game_folder, name=game_config["name"], default_map=game_config["default_map"])

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
    game.game_maps = [
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
    for location_config in map_config["locations"]:
        location = parse_location(location_config=location_config, game_map=game_map)
        game_map.add_location(location)
    return game_map
