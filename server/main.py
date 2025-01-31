from flask import Flask, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS

from GameState import GameState
from utils.logger import get_logger

logger = get_logger("server")

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

game = GameState(socketio)


@socketio.on("join_game")
def handle_join_game(data: dict):
    player_name = data["name"]

    logger.info(f"Player '{player_name}' joined.")

    game.spectators.append(player_name)
    join_room("game_room")
    emit("spectators", {"spectators": game.spectators}, room="game_room")


@socketio.on("leave_game")
def handle_leave_game(data: dict):
    player_name = data["name"]
    team_name = data["team"]

    logger.info(f"{player_name}, {team_name}")

    if team_name == "Spectator":
        game.spectators.remove(player_name)
        emit("spectators", {"spectators": game.spectators}, room="game_room")
        logger.info(f"Player '{player_name}' left.")
    elif team_name is not None:
        game.remove_player_from_team(team_name, player_name)
        emit("teams", {"teams": game.teams_to_dict_array()}, room="game_room")
        logger.info(f"Player '{player_name}' left.")


@socketio.on("join_team")
def handle_join_team(data: dict):
    player_name = data["name"]
    player_team = data["team"]

    logger.info(f"Attempting to add '{player_name}' to the {player_team} team...")

    if player_name in game.spectators:
        game.spectators.remove(player_name)
        emit("spectators", {"spectators": game.spectators}, room="game_room")
    for i, team in enumerate(game.teams):
        if team.name == player_team:
            logger.info(f"Player '{player_name}' joined the {player_team} team.")
            game.teams[i].add_player(player_name)
            break

    emit("teams", {"teams": game.teams_to_dict_array()}, room="game_room")


# Handle word submission
@socketio.on("submit_word")
def handle_word_submission(data: dict):
    word = data["word"].lower()
    team_name = data["team"]
    player_name = data["player"]

    logger.info(f"Player {player_name} from Team {team_name} submitted '{word}'.")

    if team_name != game.teams[game.current_turn].name:
        logger.info("That player is not on the current team.")
        return

    game.submit_word(team_name, player_name, word)


@app.route("/get_state", methods=["GET"])
def get_state():
    return jsonify(game.to_dict())


@app.route("/start", methods=["POST"])
def start_game():
    global game
    if not game.running:
        logger.info("Resetting...")
        game.reset()
        game.next_turn_thread = socketio.start_background_task(game.next_turn)
        return jsonify({"message": "Game started!"})
    return jsonify({"message": "Game is already running!"})


if __name__ == "__main__":
    logger.info("Booting server...")
    socketio.run(app, host="0.0.0.0", port=5000)
