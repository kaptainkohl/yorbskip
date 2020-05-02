from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import send, emit
from flask_socketio import join_room, leave_room
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!?'
socketio = SocketIO(app)

room_array = []


@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/ping')
def ping_mess():
    return render_template('ping.html')    
    
@app.route('/BattleBingo')
def battle():
    return render_template('joinGame.html') 

@app.route('/battle/', methods=['GET', 'POST'])
@app.route('/battle/<room>', methods=['GET', 'POST'])
def userpage(room=None):
	return render_template('BattleBingo.html', room=room) 
   

@app.route('/BingoStats')
def stats():
    return render_template('BingoStats.html')

@app.route('/HorizontalGoals')
def horGoals():
    return render_template('HorizontalGoals.html')     

@socketio.on('createroom')
def createroom(message):
    global room_array
    room = message
    room_array.append([room,{'var_seed':0,'var_player1':[],'var_player2':[],'var_c1':[],'var_c2':[],'running':0}])

@socketio.on('getrooms')
def showrooms(message):
    emit("showrooms",room_array)


@socketio.on('joinroom')
def test_message(message):
    print(eval(message))
    print(room_array)
    room = message
    join_room(message)
    current_room = []
    for x in room_array:
        if x[0] == message:
            current_room = x  
    emit("load", {'seed': current_room[1]['var_seed'], 'player1':current_room[1]['var_player1'],'player2':current_room[1]['var_player2'],'c1':current_room[1]['var_c1'],'c2':current_room[1]['var_c2'],'start':current_room[1]['running']},room=room);
    
@socketio.on('closeroom')
def close_message(message):
    global room_array 
    for x in room_array:
        if x[0] == message:
            current_room = x    
    room_array.remove(x)
    emit("close", broadcast=True, room=message)
    leave_room(message)
 
@socketio.on('end')
def end_message(message):
    global room_array 
    current_room = []
    for x in room_array:
        if x[0] == message['room']:
            current_room = x 
    current_room[1]['running'] = 0;
    emit("load", {'seed': current_room[1]['var_seed'], 'player1':current_room[1]['var_player1'],'player2':current_room[1]['var_player2'],'c1':current_room[1]['var_c1'],'c2':current_room[1]['var_c2'],'start':current_room[1]['running']},room=message['room']);
 
@socketio.on('clicked')
def handle_array(data):
    global room_array
    current_room = []
    for x in room_array:
        if x[0] == data['room']:
            current_room = x    
    
    current_room[1]['var_player1'] = data['p1']
    current_room[1]['var_player2'] = data['p2']
    current_room[1]['var_c1'] = data['c1']
    current_room[1]['var_c2'] = data['c2']        
    emit("newdata", data , broadcast=True,room=data['room'])
    
@socketio.on('start')
def handle_start(data):
    global room_array     
    print(data)
    print(data['data']) 
    current_room = []
    for x in room_array:
        if x[0] == data['room']:
            current_room = x  
    
    current_room[1]['var_player1'] = []
    current_room[1]['var_player2'] = []
    current_room[1]['var_c1'] = []
    current_room[1]['var_c2'] = [] 
    current_room[1]['var_seed'] = data['data']
    current_room[1]['running'] = data['start']
    
    emit("startgame", data , broadcast=True, room=data['room'])   


if __name__ == '__main__':
    socketio.run(app)