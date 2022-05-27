
from wanderer import parse_game


if __name__ == "__main__":
    # render_thingy("new_vegas", "survival")
    current_game = parse_game("new_vegas")
    routes = current_game.get_available_routes()
    route_movements = current_game.parse_route_file("survival.txt")
    print(route_movements)