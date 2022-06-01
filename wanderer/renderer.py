import math
import os
import subprocess
from typing import Tuple

from PIL import Image
from PIL.ImageDraw import ImageDraw

from wanderer.game import Movement, Game
from wanderer.position2d import Position2D
from wanderer.utils import points_between, slerp


class GameRenderer:
    def __init__(self, game: Game, output_directory: str):
        self.game = game
        self.render_index = 0
        self.frame_rate = 24
        self.extension = "jpeg"
        self.output_directory = output_directory
        self.output_image_size: Tuple[int, int] = (512, 512)
        self.map_transition_time = 0.5
        self.arrow_size = 24
        self.line_width = 3

    def render_route(self, route_name: str):
        for file in os.listdir(self.output_directory):
            if (
                file.endswith(".jpeg")
                or file.endswith(".webp")
                or file.endswith(".mp4")
            ):
                os.remove(os.path.join(self.output_directory, file))

        movements = self.game.parse_route_file(route_name)
        for movement in movements:
            print(movement)
            if (
                movement.start.game_map != movement.end.game_map
                or movement.movement_type.pixels_per_second == 0
            ):
                self.render_map_transition(
                    movement=movement,
                )
                continue

            self.render_movement(movement)

        self.render_final_zoom_out(last_movement=movements[-1])

        subprocess.run(
            [
                "ffmpeg",
                "-framerate",
                str(self.frame_rate),
                "-i",
                os.path.join(self.output_directory, f"output_%06d.{self.extension}"),
                os.path.join(self.output_directory, "final.mp4"),
                "-y",
            ]
        )

    def render_movement(self, movement: Movement):
        movement_speed = (
            movement.movement_type.pixels_per_second
            * movement.start.game_map.speed_multiplier
        ) / self.frame_rate
        points = points_between(
            movement.start.position, movement.end.position, movement_speed
        )
        base_image = movement.start.game_map.image

        for point in points:
            im: Image = base_image.copy()
            draw = ImageDraw(im)
            draw.line(
                (
                    movement.start.position.x,
                    movement.start.position.y,
                    point.x,
                    point.y,
                ),
                fill=movement.movement_type.colour_tuple(),
                width=self.line_width,
            )

            if point == points[-1]:
                movement.start.game_map.image = im.copy()

            im = self.overlay_arrow(
                im,
                start=movement.start.position,
                end=movement.end.position,
                current=point,
            )
            im: Image = im.crop(
                movement.start.game_map.get_crop_at_position(
                    point, self.output_image_size
                )
            )
            im.save(self.get_next_frame_path())

    def render_map_transition(self, movement: Movement):
        start_point, end_point = movement.start.position, movement.end.position
        base_image = movement.start.game_map.image
        overlay_image = movement.end.game_map.image

        base_crop = base_image.crop(
            movement.start.game_map.get_crop_at_position(
                start_point, self.output_image_size
            )
        )
        overlay_crop = overlay_image.crop(
            movement.end.game_map.get_crop_at_position(
                end_point, self.output_image_size
            )
        )

        frame_count = int(self.frame_rate * self.map_transition_time)
        for i in range(frame_count):
            final = Image.blend(base_crop, overlay_crop, i / frame_count)
            final.save(self.get_next_frame_path())

    def render_final_zoom_out(self, last_movement: Movement):
        game_map = last_movement.end.game_map
        movement_speed = (
            last_movement.movement_type.pixels_per_second
            * game_map.speed_multiplier
            * 0.25
        ) / self.frame_rate

        start = last_movement.end.position
        end = game_map.image_size / 2
        points = points_between(start, end, movement_speed)
        base_image = game_map.image

        image = base_image.copy()
        for point in points:
            zoom_ratio = (start - point).magnitude() / (start - end).magnitude()
            resize = slerp(
                Position2D(x=self.output_image_size[0], y=self.output_image_size[1]),
                game_map.image_size,
                zoom_ratio,
            )
            crop = image.crop(
                game_map.get_crop_at_position(point, (int(resize.x), int(resize.y)))
            )
            crop = crop.resize(self.output_image_size)
            crop.save(self.get_next_frame_path())

    def overlay_arrow(
        self, image: Image, start: Position2D, end: Position2D, current: Position2D
    ) -> Image:
        diff = end - start
        angle_between = math.atan2(diff.x, diff.y)

        with Image.open("working_images/arrow.png") as arrow_image:
            arrow_image = arrow_image.convert("RGBA")
            arrow_image = arrow_image.resize((self.arrow_size, self.arrow_size))
            arrow_image = arrow_image.rotate(math.degrees(angle_between))
            image.paste(
                arrow_image,
                (
                    int(current.x - self.arrow_size / 2),
                    int(current.y - self.arrow_size / 2),
                ),
                arrow_image.convert("RGBA"),
            )
            return image

    def get_next_frame_path(self) -> str:
        assert 0 <= self.render_index <= 10 ** 6
        filename = f"output_{self.render_index:06}.{self.extension}"
        self.render_index += 1
        return os.path.join(self.output_directory, filename)
