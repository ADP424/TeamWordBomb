import random
from threading import Thread
import threading
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS

from utils.logger import get_logger

logger = get_logger("server")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
socketio = SocketIO(app, cors_allowed_origins="*")

valid_words: dict[str, bool] = {}
valid_word_list: list[str] = []

class GameState:
    def __init__(self):
        self.teams = [
            ("Lato", []),
            ("Biny", [])
        ]
        self.spectators: list[str] = []
        self.undecideds: list[str] = []
        self.sequence_length = (2, 4)
        self.timer_length = 10 # in seconds
        self.pause_time = 0.2 # in seconds

        self.current_turn = 0
        self.current_sequence = ""
        self.running = False

        self.next_turn_stop_event = threading.Event()
        self.next_turn_thread: Thread = None

    def next_turn(self):
        logger.info("Moving to next turn...")

        self.current_turn = (self.current_turn + 1) % len(self.teams)
        self.current_sequence = self.get_random_sequence()
        socketio.emit("turn_change", {"next_team": self.teams[self.current_turn], "sequence": self.current_sequence}, room="game_room")

        if not self.running:
            logger.info("Started game...")
            self.running = True
            socketio.emit("game_started", room="game_room")

        self.start_timer()

    def start_timer(self):
        if self.running:
            for _ in range(int(self.timer_length / self.pause_time)):
                socketio.sleep(self.pause_time)
                if self.next_turn_stop_event.is_set():
                    self.next_turn_stop_event.clear()
                    logger.info("Current turn cancelled. Starting new one...")
                    socketio.start_background_task(self.next_turn)
                    return
            socketio.emit("timeout", {"team": self.teams[self.current_turn]}, room="game_room")
            socketio.start_background_task(self.next_turn)
    
    def get_random_sequence(self) -> str:
        """
        Return a random sequence of letters found in a random valid word.
        """

        random_word: str = random.choice(valid_word_list)
        sequence_length = random.randint(self.sequence_length[0], self.sequence_length[1])
        max_starting_char = len(random_word) - sequence_length
        if max_starting_char >= 0:
            starting_char = random.randint(0, max_starting_char)
            return random_word[starting_char : starting_char + sequence_length]
        else:
            return random_word

game = GameState()

def load_valid_words():
    """
    Do a one time load of all the valid words into the dictionary.
    """

    with open("server/resources/valid_words.txt", 'r') as valid_words_file:
        for line in valid_words_file.readlines():
            word = line.strip()
            valid_words[word] = True
    global valid_word_list
    valid_word_list = list(valid_words.keys())

@socketio.on("join_game")
def handle_join_game(data: dict):
    player_name = data["name"]

    logger.info(f"Player '{player_name}' joined.")

    game.undecideds.append(player_name)
    join_room("game_room")
    emit("undecideds", {"undecideds": game.undecideds}, room="game_room")

@socketio.on("join_team")
def handle_join_team(data: dict):
    player_name = data["name"]
    player_team = data["team"]

    logger.info(f"Attempting to add '{player_name}' to the {player_team} team...")

    if player_name in game.undecideds:
        game.undecideds.remove(player_name)
    elif player_name in game.spectators:
        game.spectators.remove(player_name)
    for i, team in enumerate(game.teams):
        if team[0] == player_team:
            logger.info(f"Player '{player_name}' joined the {player_team} team.")
            game.teams[i][1].append(player_name)
            break

    emit("teams", {"teams": game.teams}, room="game_room")

# Handle word submission
@socketio.on("submit_word")
def handle_word_submission(data: dict):
    word = data["word"].upper()
    team = data["team"]
    player = data["player"]

    logger.info(f"Player {player} from Team {team} submitted '{word}'.")

    if team != game.teams[game.current_turn][0]:
        logger.info("That player is not on the current team.")
        return

    if valid_words.get(word, False) and game.current_sequence in word:
        logger.info(f"{game.current_sequence} is in {word}.")
        socketio.emit("valid_word", {"team": team, "player": player, "word": word}, room="game_room")
        game.next_turn_stop_event.set()
    else:
        socketio.emit("invalid_word", {"team": team, "player": player, "word": word}, room="game_room")

# Start the game
@app.route("/start", methods=["POST"])
def start_game():
    if not game.running:
        game.next_turn_thread = socketio.start_background_task(game.next_turn)
        return jsonify({"message": "Game started!"})
    return jsonify({"message": "Game is already running!"})

if __name__ == "__main__":
    logger.info("Loading valid words...")
    load_valid_words()
    logger.info("Booting server...")
    socketio.run(app, host="0.0.0.0", port=5000)
