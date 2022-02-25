import os
from PIL import Image
from PIL.ImageDraw import ImageDraw


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

    with Image.open(map_file) as im:
        draw = ImageDraw(im)
        draw.line((0, 0) + im.size, fill=128)
        draw.line((0, im.size[1], im.size[0], 0), fill=128)

        output_file = os.path.join(output_directory, "output.jpeg")
        im.save(output_file, "jpeg")


if __name__ == "__main__":
    render_thingy("new_vegas", "survival")
