import logging
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = '64afd5d3e8d7c3b949e3127602068d93db31c9fdfdb6c53a329e39d245be8652'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active rooms and connections
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create or join')
def on_create_or_join(room_id):
    logging.debug(f"Attempting to join or create room: {room_id} by user {request.sid}")
    
    # Manage room joining
    if room_id not in rooms:
        rooms[room_id] = set()
        logging.info(f"Created a new room: {room_id}")
    
    # Limit room to 2 participants
    if len(rooms[room_id]) < 2:
        join_room(room_id)
        rooms[room_id].add(request.sid)
        logging.info(f"User {request.sid} joined room {room_id}")
        
        # Notify other room members
        other_users = list(rooms[room_id] - {request.sid})
        if other_users:
            emit('room members', other_users, room=request.sid)
            emit('new peer', request.sid, room=other_users[0])
            logging.debug(f"Notified room members {other_users} about the new peer {request.sid}")
    else:
        emit('room full')
        logging.warning(f"Room {room_id} is full. User {request.sid} couldn't join.")

@socketio.on('signal')
def on_signal(data):
    logging.debug(f"Relaying signaling data from {request.sid} to {data['to']}")
    # Relay WebRTC signaling messages
    emit('signal', {
        'from': request.sid,
        'signal': data['signal']
    }, room=data['to'])

@socketio.on('disconnect')
def on_disconnect():
    logging.info(f"User {request.sid} disconnected")
    
    # Remove user from rooms on disconnect
    for room_id, room_users in rooms.items():
        if request.sid in room_users:
            room_users.remove(request.sid)
            logging.info(f"User {request.sid} removed from room {room_id}")
            if not room_users:
                del rooms[room_id]
                logging.info(f"Room {room_id} is empty and deleted")

if __name__ == '__main__':
    socketio.run(app, debug=True)
