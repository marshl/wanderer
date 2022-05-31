import math
import os
import subprocess

from PIL import Image
from PIL.ImageDraw import ImageDraw

from wanderer.game import Movement, Game
from wanderer.utils import points_between, lerp
from wanderer.position2d import Position2D


class GameRenderer:

    def __init__(self, game: Game):
        self.game = game

    def render_route(self, route_name: str, output_directory: str):
        for file in os.listdir(output_directory):
            if (
                file.endswith(".jpeg")
                or file.endswith(".webp")
                or file.endswith(".mp4")
            ):
                os.remove(os.path.join(output_directory, file))

        frame_rate = 24

        movements = self.game.parse_route_file(route_name)
        index = 0
        extension = "jpeg"
        for movement in movements:
            if movement.start.game_map != movement.end.game_map:
                index = self.render_map_transition(
                    movement=movement,
                    current_index=index,
                    output_directory=output_directory,
                    extension=extension,
                    frame_rate=frame_rate,
                )
                # TODO: Some kind of map transition
                continue
            print(movement)
            index = self.render_movement(
                movement,
                current_index=index,
                output_directory=output_directory,
                frame_rate=frame_rate,
                extension=extension,
            )

        index = self.render_final_zoom_out(
            last_movement=movements[-1],
            current_index=index,
            output_directory=output_directory,
            frame_rate=frame_rate,
            extension=extension,
        )

        subprocess.run(
            [
                "ffmpeg",
                "-framerate",
                str(frame_rate),
                "-i",
                os.path.join(output_directory, f"output_%06d.{extension}"),
                os.path.join(output_directory, "final.mp4"),
                "-y",
            ]
        )

    def render_movement(
        self,
        movement: Movement,
        current_index: int,
        output_directory: str,
        frame_rate: int,
        extension: str,
    ) -> int:
        movement_speed = (
            movement.movement_type.pixels_per_second
            * movement.start.game_map.speed_multiplier
        ) / frame_rate
        points = points_between(
            movement.start.position, movement.end.position, movement_speed
        )
        base_image = movement.start.game_map.image

        for point in points:
            im = base_image.copy()
            draw = ImageDraw(im)
            draw.line(
                (
                    movement.start.position.x,
                    movement.start.position.y,
                    point.x,
                    point.y,
                ),
                fill=movement.movement_type.colour_tuple(),
            )

            output_file = os.path.join(
                output_directory,
                self.get_output_filename(current_index, extension=extension),
            )
            current_index += 1
            if point == points[-1]:
                movement.start.game_map.image = im.copy()
            im = self.overlay_arrow(
                im,
                start=movement.start.position,
                end=movement.end.position,
                current=point,
            )
            crop = im.crop(
                movement.start.game_map.get_crop_at_position(point, (512, 512))
            )
            crop.save(output_file, extension)

        return current_index

    def render_map_transition(
        self,
        movement: Movement,
        current_index: int,
        output_directory: str,
        frame_rate: int,
        extension: str,
    ) -> int:
        start_point, end_point = movement.start.position, movement.end.position
        base_image = movement.start.game_map.image
        overlay_image = movement.end.game_map.image

        base_crop = base_image.crop(
            movement.start.game_map.get_crop_at_position(start_point, (512, 512))
        )
        overlay_crop = overlay_image.crop(
            movement.end.game_map.get_crop_at_position(end_point, (512, 512))
        )

        frame_count = int(frame_rate / 2)
        for i in range(frame_count):
            final = Image.blend(base_crop, overlay_crop, i / frame_count)
            output_file = os.path.join(
                output_directory,
                self.get_output_filename(current_index, extension=extension),
            )
            current_index += 1
            final.save(output_file, extension)

        return current_index

    def render_final_zoom_out(
        self,
        last_movement: Movement,
        current_index: int,
        output_directory: str,
        frame_rate: int,
        extension: str,
    ) -> int:
        game_map = last_movement.end.game_map
        movement_speed = (
            last_movement.movement_type.pixels_per_second
            * game_map.speed_multiplier
            * 0.5
        ) / frame_rate

        start = last_movement.end.position
        end = game_map.image_size / 2
        points = points_between(start, end, movement_speed)
        base_image = game_map.image

        for point in points:
            im = base_image.copy()
            output_file = os.path.join(
                output_directory,
                self.get_output_filename(current_index, extension=extension),
            )
            current_index += 1

            zoom_ratio = (start - point).magnitude() / (start - end).magnitude()
            resize = lerp(Position2D(x=512, y=512), game_map.image_size, zoom_ratio)
            crop = im.crop(
                game_map.get_crop_at_position(point, (int(resize.x), int(resize.y)))
            )
            crop = crop.resize((512, 512))
            crop.save(output_file, extension)

        return current_index

    def overlay_arrow(
        self, image: Image, start: Position2D, end: Position2D, current: Position2D
    ) -> Image:
        diff = end - start
        angle_between = math.atan2(diff.x, diff.y)
        arrow_size = 24

        with Image.open("working_images/arrow.png") as arrow_image:
            arrow_image = arrow_image.convert("RGBA")
            arrow_image = arrow_image.resize((arrow_size, arrow_size))
            arrow_image = arrow_image.rotate(math.degrees(angle_between))
            image.paste(
                arrow_image,
                (int(current.x - arrow_size / 2), int(current.y - arrow_size / 2)),
                arrow_image.convert("RGBA"),
            )
            return image

    def get_output_filename(self, index: int, extension: str):
        assert 0 <= index <= 100000
        return f"output_{index:06}.{extension}"
