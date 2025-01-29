import socketio

sio = socketio.Client()

@sio.on("connect")
def on_connect():
    print("Connected to server")
    sio.emit("join_game", {"name": "Player1"})

@sio.on("turn_change")
def on_turn_change(data):
    print(f"Turn changed! Next player: {data['next_player']}")

@sio.on("valid_word")
def on_valid_word(data):
    print(f"{data['player']} submitted a valid word: {data['word']}")

@sio.on("invalid_word")
def on_invalid_word(data):
    print(f"{data['player']} submitted an invalid word: {data['word']}")

@sio.on("timeout")
def on_timeout(data):
    print(f"{data['player']} ran out of time!")

sio.connect("http://localhost:5000")
