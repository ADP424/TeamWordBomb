import React, { useState, useEffect } from "react";
import io from "socket.io-client";

const socket = io("http://localhost:5000");

const Game = () => {
  // game info
  const [teams, setTeams] = useState([]);
  const [spectators, setSpectators] = useState([]);
  const [undecideds, setUndecideds] = useState([]);
  const [gameStarted, setGameStarted] = useState(false);
  const [gameSequence, setGameSequence] = useState("");

  // player info
  const [playerName, setPlayerName] = useState("");
  const [team, setTeam] = useState(null);
  const [currentTeam, setCurrentTeam] = useState(null);
  const [word, setWord] = useState("");

  useEffect(() => {
    socket.on("teams", (data) => {
      setTeams(data.teams);
      console.log("Teams data was updated.")
    });

    socket.on("spectators", (data) => {
      setSpectators(data.spectators);
      console.log("Spectator data was updated.")
    });

    socket.on("undecideds", (data) => {
      setUndecideds(data.undecideds);
      console.log("Undecideds data was updated.")
    });

    socket.on("game_started", () => {
      setGameStarted(true);
      console.log("Game was started.")
    });

    socket.on("turn_change", (data) => {
      setCurrentTeam(data.next_team);
      setGameSequence(data.sequence);
      console.log("Turn was changed.")
    });

    socket.on("valid_word", (data) => {
      console.log(`${data.player} from ${data.team} submitted a valid word: ${data.word}`);
    });

    socket.on("invalid_word", (data) => {
      console.log(`${data.player} from ${data.team} submitted an invalid word: ${data.word}`);
    });

    socket.on("timeout", (data) => {
      console.log(`Time's up! Team ${data.team} ran out of time.`);
    });

    return () => {
      socket.off("spectators");
      socket.off("game_started");
      socket.off("turn_change");
      socket.off("valid_word");
      socket.off("invalid_word");
      socket.off("timeout");
    };
  }, []);

  const joinGame = () => {
    if (playerName) {
      setTeam("Undecided")
      socket.emit("join_game", { name: playerName });
    }
  };

  const joinTeam = (team) => {
    if (playerName) {
      setTeam(team)
      socket.emit("join_team", { name: playerName, team: team });
    }
  };

  const startGame = async () => {
    try {
      const response = await fetch("http://localhost:5000/start", {
        method: "POST",
      });
      const data = await response.json();
      console.log(data.message);
    } catch (error) {
      console.error("Error starting game:", error);
    }
  };

  const submitWord = () => {
    if (word && team) {
      socket.emit("submit_word", { player: playerName, team, word });
      setWord("");
    }
  };

  return (
    <div>
      {!team ? (
        <div>
          <h2>Enter Your Name</h2>
          <input type="text" onChange={(e) => setPlayerName(e.target.value)} />
          <button onClick={joinGame}>Enter</button>
        </div>
      ) : (
        <div>
          <h2>Welcome, {playerName}!</h2>
          {!team || team === "Undecided" ? (
            <div>
              <h3>Select a Team</h3>
              <button onClick={() => joinTeam("Lato")}>Join Lato Team</button>
              <button onClick={() => joinTeam("Biny")}>Join Biny Team</button>
              <button onClick={() => joinTeam("Spectator")}>Join as a Spectator</button>
            </div>
          ) : (
            <div>
              {team === "Spectator" ? (
                <h3>You are a Spectator</h3>
              ) : (
                <div>
                  <h3>You are on {team} Team</h3>
                  <button onClick={() => startGame()}>Start Game</button>
                </div>
              )}
            </div>
          )}

          {gameStarted ? (
            <div>
              <h3>Current Turn: {currentTeam[0]}</h3>
              <p>Type a word containing: <strong>{gameSequence}</strong></p>
              <input
                type="text"
                value={word}
                onChange={(e) => setWord(e.target.value)}
              />
              <button onClick={submitWord}>Submit Word</button>
            </div>
          ) : (
            <div></div>
          )}
        </div>
      )}
    </div>
  );
};

export default Game;
