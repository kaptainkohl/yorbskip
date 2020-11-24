from flask import Flask, render_template
from flask import request
from flask_socketio import SocketIO
from flask_socketio import send, emit
from flask_socketio import join_room, leave_room
import json
import datetime
import time
from google.cloud import storage

client = storage.Client()
bucket = client.get_bucket('my-project-1474166845942.appspot.com')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'This is a super secret hash for my logins'
socketio = SocketIO(app)

room_array = []
bingo_array = []

time_delay = datetime.datetime.now()
user_delay = ""

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/ping')
def ping_mess():
    return render_template('ping.html')    
    
@app.route('/bingo',methods=['GET', 'POST'])
def bingo_card():
    return render_template('bingo.html') 

@app.route('/bingoShot',methods=['GET', 'POST'])
def bingoStab_card():
    return render_template('bingoStab.html') 
  
@app.route('/popout',methods=['GET', 'POST'])
def bingo_pop():
    return render_template('popout.html')      

@app.route('/lines_popout',methods=['GET', 'POST'])
def line_pop():
    return render_template('lines_popout.html')       

@app.route('/sync',methods=['GET', 'POST'])
def bingo_sync():
    return render_template('synclobby.html') 
    
@app.route('/lines',methods=['GET', 'POST'])
def lines():
    return render_template('lines.html') 

@app.route('/sendData',methods=['GET', 'POST'])
def sendData():
    global time_delay 
    date = datetime.datetime.now()
    if date > time_delay:
        time_delay = date + datetime.timedelta(seconds=(5))        
        timestamp = request.form['time']
        rowcol = request.form['rowcol']
        card = request.form['card']
        seed = request.form['cardseed']
        version = request.form['version']
        user = request.form['user']
        blob = bucket.get_blob('bingo_data.txt')
        blob2 = bucket.get_blob('bingo_data.txt')
        file = str(blob2.download_as_string())
        file_to_write = file + version+"@"+date.strftime("%c")+"@"+seed+"@"+rowcol+"@"+timestamp+"@"+user+"@"+card+'$'
        while file_to_write[0] == 'b' or file_to_write[0] == "'" or file_to_write[0] == '"':
            file_to_write = file_to_write[1:]
        blob.upload_from_string(file_to_write)
    return render_template('dataSent.html') 


@app.route('/bingoData',methods=['GET', 'POST'])
def bingoData():
    blob2 = bucket.get_blob('bingo_data.txt')
    file = blob2.download_as_string()
    return render_template('bingoData.html',data=file)  
    
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
    room_array.remove(current_room)
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