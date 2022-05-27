from typing import List

from wanderer.position2d import Position2D


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
