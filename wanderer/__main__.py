from wanderer.game import parse_game
from wanderer.renderer import GameRenderer

if __name__ == "__main__":
    current_game = parse_game("new_vegas")
    routes = current_game.get_available_routes()
    route_movements = current_game.parse_route_file("survival.txt")
    renderer = GameRenderer(current_game, output_directory="output")
    renderer.render_route("survival.txt")
