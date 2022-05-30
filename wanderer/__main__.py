from wanderer import parse_game


if __name__ == "__main__":
    current_game = parse_game("new_vegas")
    routes = current_game.get_available_routes()
    route_movements = current_game.parse_route_file("survival.txt")
    current_game.render_route("survival.txt", "output")
