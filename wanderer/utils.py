import math
from typing import List, Any

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
    if points[-1] == end:
        return points
    return points + [end]
