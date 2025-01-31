class Team:
    def __init__(self, name: str, lives: int):
        self.name = name
        self.lives = lives
        self.players: list[str] = []
        self.alive = True

    def add_player(self, player: str) -> bool:
        """
        Add a player to the team if they aren't already in.
        Return whether the player was added or not.
        """

        if player not in self.players:
            self.players.append(player)
            return True
        return False

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.alive = False

    def to_dict(self):
        return {
            "name": self.name,
            "lives": self.lives,
            "players": self.players,
            "alive": self.alive,
        }
