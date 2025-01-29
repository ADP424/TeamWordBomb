from logging import Logger
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import time
import threading

logger = Logger("server")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

game_state = {
    "players": [],
    "current_turn": 0,
    "sequence": "ab",
    "timer": None,
    "running": False
}

# Timer Thread Function
def start_timer():
    time.sleep(10)  # Example: 10-second timer
    socketio.emit("timeout", {"player": game_state["players"][game_state["current_turn"]]})
    next_turn()

# Move to the next turn
def next_turn():
    logger.info("Moving to next turn...")

    game_state["current_turn"] = (game_state["current_turn"] + 1) % len(game_state["players"])
    socketio.emit("turn_change", {"next_player": game_state["players"][game_state["current_turn"]]})
    start_timer()

# Handle player joining
@socketio.on("join_game")
def handle_join(data):
    player_name = data["name"]

    logger.info(f"Player {player_name} joined.")

    game_state["players"].append(player_name)
    join_room("game_room")
    emit("player_list", {"players": game_state["players"]}, broadcast=True)

# Handle word submission
@socketio.on("submit_word")
def handle_word_submission(data):
    word = data["word"]
    player = data["player"]

    logger.info(f"Player {player} submitted '{word}'.")

    if game_state["sequence"] in word:
        socketio.emit("valid_word", {"player": player, "word": word}, broadcast=True)
        next_turn()
    else:
        socketio.emit("invalid_word", {"player": player, "word": word}, broadcast=True)

# Start the game
@app.route("/start", methods=["POST"])
def start_game():
    if not game_state["running"]:
        game_state["running"] = True
        socketio.emit("game_started", {"sequence": game_state["sequence"]})
        next_turn()
        return jsonify({"message": "Game started!"})
    return jsonify({"message": "Game is already running!"})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
