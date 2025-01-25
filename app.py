import logging
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.config['SECRET_KEY'] = '64afd5d3e8d7c3b949e3127602068d93db31c9fdfdb6c53a329e39d245be8652'
socketio = SocketIO(app, cors_allowed_origins="*")

# Active rooms and user connections
rooms = {}

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@socketio.on('create or join')
def on_create_or_join(room_id):
    """Handle requests to create or join a room."""
    logging.info(f"User {request.sid} requested to join or create room: {room_id}")

    if room_id not in rooms:
        rooms[room_id] = set()
        logging.info(f"Room {room_id} created.")

    if len(rooms[room_id]) < 2:
        join_room(room_id)
        rooms[room_id].add(request.sid)
        logging.info(f"User {request.sid} joined room {room_id}. Current members: {rooms[room_id]}")

        # Notify others in the room
        other_users = list(rooms[room_id] - {request.sid})
        if other_users:
            emit('room members', other_users, room=request.sid)
            emit('new peer', request.sid, room=other_users[0])
            logging.debug(f"Notified existing members {other_users} about new peer {request.sid}.")
    else:
        emit('room full')
        logging.warning(f"Room {room_id} is full. User {request.sid} could not join.")

@socketio.on('signal')
def on_signal(data):
    """Relay WebRTC signaling messages."""
    target_sid = data['to']
    logging.debug(f"Relaying signaling data from {request.sid} to {target_sid}.")
    emit('signal', {
        'from': request.sid,
        'signal': data['signal']
    }, room=target_sid)

@socketio.on('disconnect')
def on_disconnect():
    """Handle user disconnection."""
    logging.info(f"User {request.sid} disconnected.")

    # Remove the user from any rooms they are part of
    for room_id, room_users in list(rooms.items()):
        if request.sid in room_users:
            room_users.remove(request.sid)
            logging.info(f"User {request.sid} removed from room {room_id}. Remaining members: {room_users}")
            
            if not room_users:
                del rooms[room_id]
                logging.info(f"Room {room_id} is now empty and has been deleted.")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)
