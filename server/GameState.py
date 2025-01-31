import random
import threading

from flask_socketio import SocketIO

from Team import Team
from utils.logger import get_logger

logger = get_logger("game-state")


class GameState:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio

        logger.info("Loading valid words...")
        self.valid_words: dict[str, bool] = {}
        self.load_valid_words()

        logger.info("Loading sequences...")
        self.sequences: list[str] = []
        self.load_sequences()
        
        self.starting_lives = 3
        self.teams = [
            Team("Lato", self.starting_lives),
            Team("Biny", self.starting_lives),
        ]

        self.reset()

    def next_turn(self):
        logger.info("Moving to next turn...")

        self.current_turn = (self.current_turn + 1) % len(self.teams)
        if not (0 < self.current_sequence_failures < len(self.teams)):
            self.current_sequence = self.get_random_sequence()
        self.socketio.emit(
            "turn_change",
            {"next_team": self.teams[self.current_turn].to_dict(), "sequence": self.current_sequence},
            room="game_room",
        )

        if not self.running:
            logger.info("Started game...")
            self.running = True
            self.socketio.emit("game_started", {"teams": self.teams_to_dict_array()}, room="game_room")

        self.start_timer()

    def start_timer(self):
        if self.running:
            for _ in range(int(self.timer_length / self.pause_time)):
                self.socketio.sleep(self.pause_time)
                if self.next_turn_stop_event.is_set():
                    self.next_turn_stop_event.clear()
                    logger.info("Current turn cancelled. Starting new one...")
                    self.socketio.start_background_task(self.next_turn)
                    return

            self.teams[self.current_turn].lose_life()
            self.current_sequence_failures += 1
            self.socketio.emit(
                "timeout",
                {"team": self.teams[self.current_turn].to_dict(), "teams": self.teams_to_dict_array()},
                room="game_room",
            )

            last_team = self.one_team_remaining()
            if last_team:
                self.socketio.emit("game_over", {"team": last_team.to_dict()})
                self.running = False
            else:
                self.socketio.start_background_task(self.next_turn)

    def add_player_to_team(self, team_name: str, player_name: str) -> bool:
        """
        Add the given player to the given team and remove them from all other teams/spectators.
        Return whether the player was added or not.
        """

        if player_name in self.spectators:
            self.spectators.remove(player_name)
        team = self.get_team(team_name)
        return team.add_player(player_name)

    def remove_player_from_team(self, team_name: str, player_name: str):
        """
        Remove the given player from the given team.
        """

        team = self.get_team(team_name)
        team.players.remove(player_name)

    def submit_word(self, team_name: str, player_name: str, word: str):
        """
        Submit a word and emit the submission to all listeners.
        """

        team = self.get_team(team_name)
        if not self.valid_words.get(word, False):
            self.socketio.emit(
                "invalid_word",
                {"team": team.to_dict(), "player": player_name, "word": word, "reason": "not_in_dictionary"},
                room="game_room",
            )
        elif self.current_sequence not in word:
            self.socketio.emit(
                "invalid_word",
                {"team": team.to_dict(), "player": player_name, "word": word, "reason": "sequence_not_in_word"},
                room="game_room",
            )
        elif word in self.used_words:
            self.socketio.emit(
                "invalid_word",
                {"team": team.to_dict(), "player": player_name, "word": word, "reason": "word_already_used"},
                room="game_room",
            )
        else:
            self.current_sequence_failures = 0
            self.used_words[word] = True
            self.socketio.emit(
                "valid_word",
                {"team": team.to_dict(), "player": player_name, "word": word, "reason": "valid"},
                room="game_room",
            )
            self.next_turn_stop_event.set()

    def one_team_remaining(self) -> Team | bool:
        """
        Returns the last team remaining.
        Returns False if more than one team is remaining.
        """

        alive_team = None
        for team in self.teams:
            if team.alive:
                if alive_team is not None:
                    return False
                alive_team = team
        return alive_team

    def reset(self):
        for i in range(len(self.teams)):
            self.teams[i].alive = True
            self.teams[i].lives = self.starting_lives
        
        self.spectators: list[str] = []
        self.sequence_length = (2, 4)
        self.timer_length = 10  # in seconds
        self.pause_time = 0.2  # in seconds

        self.current_turn = -1
        self.current_sequence = ""
        self.current_sequence_failures = 0
        self.used_words: dict[str, bool] = {}
        self.running = False

        self.next_turn_stop_event = threading.Event()
        self.next_turn_thread: threading.Thread = None

    def get_random_sequence(self) -> str:
        """
        Return a random sequence from `sequences_300.txt`.
        """

        return random.choice(self.sequences)

    def get_team(self, team_name: str) -> Team | None:
        """
        Return the Team object with the given name.
        Return None if no Team with that name exists.
        """

        return next((t for t in self.teams if t.name == team_name), None)

    def load_valid_words(self):
        """
        Do a one time load of all the valid words into the dictionary.
        """

        with open("resources/valid_words.txt", "r") as valid_words_file:
            for line in valid_words_file.readlines():
                word = line.strip()
                self.valid_words[word] = True

    def load_sequences(self):
        """
        Do a one time load of all the sequences into the list.
        """

        with open("resources/sequences_300.txt", "r") as sequences_file:
            for line in sequences_file.readlines():
                seq = line.strip()
                self.sequences.append(seq)

    def to_dict(self):
        return {
            "teams": self.teams_to_dict_array(),
            "spectators": self.spectators,
            "sequence_length": self.sequence_length,
            "timer_length": self.timer_length,
            "pause_time": self.pause_time,
            "current_turn": self.current_turn,
            "current_sequence": self.current_sequence,
            "running": self.running,
        }

    def teams_to_dict_array(self):
        return [team.to_dict() for team in self.teams]
