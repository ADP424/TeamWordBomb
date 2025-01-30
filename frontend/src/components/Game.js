import React, { useState, useEffect } from "react";
import Countdown from 'react-countdown';
import io from "socket.io-client";
import TeamDisplay from "./TeamDisplay";

import 'bootstrap/dist/css/bootstrap.min.css';
import Container from "react-bootstrap/Container";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import Card from "react-bootstrap/Card";

const socket = io("http://localhost:5000");

const Game = () => {
  // game info
  const [teams, setTeams] = useState([]);
  const [spectators, setSpectators] = useState([]);
  const [gameStarted, setGameStarted] = useState(false);
  const [currentSequence, setCurrentSequence] = useState("");
  const [currentTeam, setCurrentTeam] = useState(null);
  const [timerLength, setTimerLength] = useState(10);
  const [timerKey, setTimerKey] = useState(Date.now() + timerLength);

  // player info
  const [playerName, setPlayerName] = useState("");
  const [playerTeam, setPlayerTeam] = useState(null);
  const [word, setWord] = useState("");
  const [undecided, setUndecided] = useState(true);

  useEffect(() => {
    socket.on("teams", (data) => {
      setTeams(data.teams);
    });

    socket.on("spectators", (data) => {
      setSpectators(data.spectators);
    });

    socket.on("game_started", () => {
      setGameStarted(true);
    });

    socket.on("turn_change", (data) => {
      setCurrentTeam(data.next_team);
      setCurrentSequence(data.sequence);
      setTimerKey(Date.now() + timerLength * 1000);
    });

    socket.on("valid_word", (data) => {
      console.log(`${data.player} from ${data.team} submitted a valid word: ${data.word}`);
    });

    socket.on("invalid_word", (data) => {
      console.log(`${data.player} from ${data.team} submitted an invalid word: ${data.word}`);
    });

    socket.on("timeout", (data) => {
      console.log(`Time's up! Team ${data.team} ran out of time.`);
      setTeams(data.teams)
      setTimerKey(Date.now() + timerLength * 1000);
      console.log(timerLength)
    });

    const fetchGameData = async () => {
      try {
        const response = await fetch("http://localhost:5000/get_state", {
          method: "GET",
        });
        const gameState = await response.json();
        setTeams(gameState.teams);
        setSpectators(gameState.spectators);
        setTimerLength(gameState.timer_length);
        setGameStarted(gameState.running);
        setCurrentSequence(gameState.current_sequence);
        setCurrentTeam(gameState.teams[gameState.current_turn]);
      } catch (error) {
        console.error("Error starting game:", error);
      }
    };

    fetchGameData();

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
      setPlayerTeam("Spectator");
      socket.emit("join_game", { name: playerName });
    }
  };

  const joinTeam = (team) => {
    if (playerName) {
      setPlayerTeam(team);
      setUndecided(false);
      if (team !== "Spectator") {
        socket.emit("join_team", { name: playerName, team: team });
      }
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
    if (word && playerTeam) {
      socket.emit("submit_word", { player: playerName, team: playerTeam, word: word });
      setWord("");
    }
  };

  return (
    <Container>
      <Row>
        <Col md={4} lg={4}></Col>

        <Col md={4} lg={4} className="perfect-center">
          {!playerTeam ? (
            <EnterName setPlayerName={setPlayerName} joinGame={joinGame} />
          ) : (
            <GameInterface
              playerName={playerName}
              playerTeam={playerTeam}
              undecided={undecided}
              joinTeam={joinTeam}
              gameStarted={gameStarted}
              currentTeam={currentTeam}
              currentSequence={currentSequence}
              word={word}
              setWord={setWord}
              submitWord={submitWord}
              startGame={startGame}
              timerKey={timerKey}
            />
          )}
        </Col>

        <Col md={4} lg={4} className="perfect-center">
          <TeamDisplay teams={teams} spectators={spectators} />
        </Col>
      </Row>
    </Container>
  );
};

const EnterName = ({ setPlayerName, joinGame }) => (
  <div className="center-content">
    <h2>Enter Your Name</h2>
    <input
      type="text"
      onChange={(e) => setPlayerName(e.target.value)}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          joinGame();
        }
      }}
    />
    <button onClick={joinGame}>Enter</button>
  </div>
);

const GameInterface = ({
  playerName,
  playerTeam,
  undecided,
  joinTeam,
  gameStarted,
  currentTeam,
  currentSequence,
  word,
  setWord,
  submitWord,
  startGame,
  timerKey
}) => (
  <Card text="dark" className="main-card center-content my-3 mx-auto">
    <Card.Header as="h2">{playerName}</Card.Header>
    {undecided ? (
      <SelectTeam joinTeam={joinTeam} />
    ) : (
      <div>
        {playerTeam === "Spectator" ? (
          <h3>You are a Spectator</h3>
        ) : (
          <div>
            <h3>You are on {playerTeam} Team</h3>
            <button onClick={startGame}>Start Game</button>
          </div>
        )}
      </div>
    )}
    {
      gameStarted && 
      <WordSubmission 
        currentTeam={currentTeam} 
        currentSequence={currentSequence} 
        word={word} 
        setWord={setWord} 
        submitWord={submitWord} 
        timerKey={timerKey}
      />
    }
  </Card>
);

const SelectTeam = ({ joinTeam }) => (
  <div>
    <h3>Select a Team</h3>
    <button onClick={() => joinTeam("Lato")}>Join Lato Team</button>
    <button onClick={() => joinTeam("Biny")}>Join Biny Team</button>
    <button onClick={() => joinTeam("Spectator")}>Join as a Spectator</button>
  </div>
);

const WordSubmission = ({ currentTeam, currentSequence, word, setWord, submitWord, timerKey }) => (
  <div>
    <h3>Current Turn: {currentTeam?.[0]}</h3>
    <Countdown
      key={timerKey}
      date={timerKey}
      intervalDelay={0}
      precision={1}
      renderer={({ seconds, milliseconds }) => (
        <div style={{ fontSize: "4rem", fontWeight: "bold" }}>
          {seconds}.{Math.floor(milliseconds / 100)}
        </div>
      )}
    />
    <p>Type a word containing: <strong>{currentSequence}</strong></p>
    <input 
      type="text" value={word} 
      onChange={(e) => setWord(e.target.value)} 
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          submitWord();
        }
      }}
    />
    <button onClick={submitWord}>Submit Word</button>
  </div>
);

export default Game;
