import React from "react";
import Container from "react-bootstrap/Container";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import Card from "react-bootstrap/Card";

const TeamDisplay = ({ teams, spectators }) => {
    return (
        <Container>

            <Row className="mb-4">
                <Col>
                    <Card bg="warning" text="dark" className="mb-3">
                        <Card.Header as="h5">Teams</Card.Header>
                        <Card.Body>
                            {teams.map((team, index) => (
                                <div key={index} className="mb-3">
                                    <h5>{team[0]} ({team[2] > 0 ? "❤️ " + team[2] : "💀"})</h5>
                                    <ul>
                                        {team[1].map((player, playerIndex) => (
                                            <li key={playerIndex}>{player}</li>
                                        ))}
                                    </ul>
                                </div>
                            ))}
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Row className="mb-4">
                <Col>
                    <Card bg="secondary" text="white" className="mb-3">
                        <Card.Header as="h5">Spectators</Card.Header>
                        <Card.Body>
                            <ul>
                                {spectators.map((spectator, index) => (
                                    <li key={index}>{spectator}</li>
                                ))}
                            </ul>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default TeamDisplay;
