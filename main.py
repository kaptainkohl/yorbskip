from flask import Flask, render_template, jsonify
from flask import request
from flask_socketio import SocketIO
from flask_socketio import send, emit
from flask_socketio import join_room, leave_room
import json
import datetime
import time
import requests
from bs4 import BeautifulSoup
from google.cloud import storage


client = storage.Client()
bucket = client.get_bucket('my-project-1474166845942.appspot.com')

# $env:FLASK_APP = "main.py"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'This is a super secret hash for my logins'
socketio = SocketIO(app)

room_array = []
bingo_array = []

time_delay = datetime.datetime.now()
user_delay = ""

player_data = []

start_time = 0

previous_data = ""

lockout = {}


def start_timer():
    global start_time
    start_time = datetime.datetime.now()


def stop_timer():
    global start_time
    start_time = 0

def read_timer():
    if start_time == 0:
        return 0
    return int(datetime.datetime.now().timestamp() - start_time.timestamp())

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/ping')
def ping_mess():
    return render_template('ping.html')

# ---------LOCKOUT---------------------
@app.route('/lock_ping',methods=['GET', 'POST'])
def lock_ping():
    global lockout
    room = request.args.get('room','-1')
    if room in lockout:
        return jsonify(result=lockout[room])
    return "no room found"

@app.route('/lock_update',methods=['GET', 'POST'])
def lock_update():
    global lockout
    room = request.args.get('room','-1')
    num = request.args.get('num','-1')
    color = request.args.get('color','delete')
    if room in lockout:
        if num in lockout:
            if color == "delete":
                lockout[room].remove(num)
        else:
            lockout[room][num] = color   
    else:
        lockout[room] = {}
        lockout[room][num] = color
    
    return jsonify(result=lockout[room])

@app.route('/lock_clear',methods=['GET', 'POST'])
def lock_clear():
    global lockout
    room = request.args.get('room','-1')
    if room in lockout:
        lockout[room] = {}
    return "Cleared"



@app.route('/_timerStart')
def time_mess():
    start_timer()
    return jsonify(result="start")

@app.route('/_timerStop')
def timestop_mess():
    stop_timer()
    return jsonify(result="stop")


@app.route('/usercontrol')
def user_control():
    return render_template('usercontrol.html')

@app.route('/scheduler')
def scheduler():
    return render_template('schedule.html')

@app.route('/bitclip')
def bitclip():
    return render_template('bitclip.html')

@app.route('/patterns')
def pattern():
    return render_template('pattern.html')

@app.route('/lake')
def lake():
    return render_template('lake.html')

@app.route('/lakelevel')
def lakelevel():
    URL = 'https://www.laketexoma.com/water_level_widget.php'
    page = requests.get(URL)
    
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('p')
    level = results[0].get_text()[-10:]

    return jsonify(result=level)

@app.route('/info',methods=['GET', 'POST'])
def info():
    return render_template('bingoInfo.html')

@app.route('/tracker')
def puzzle():
    return render_template('puzzle.html')

@app.route('/contest/')
@app.route('/contest/<room>/')
@app.route('/contest/<room>/<user>')
def contest(room="",user=""):
    return render_template('contest.html', room=room, user=user)

@app.route('/bingo',methods=['GET', 'POST'])
def bingo_card():
    return render_template('bingo.html')

@app.route('/bingoTEST',methods=['GET', 'POST'])
def bingo_Test():
    return render_template('testBingo.html')
  
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
        time_delay = date + datetime.timedelta(seconds=(2))        
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
        file_to_write = file_to_write.replace("\\","")
        file_to_write = file_to_write.replace("'","")
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
    emit("load", {'seed': current_room[1]['var_seed'], 'player1':current_room[1]['var_player1'],'player2':current_room[1]['var_player2'],'c1':current_room[1]['var_c1'],'c2':current_room[1]['var_c2'],'start':current_room[1]['running']},room=room)
    
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
    current_room[1]['running'] = 0
    emit("load", {'seed': current_room[1]['var_seed'], 'player1':current_room[1]['var_player1'],'player2':current_room[1]['var_player2'],'c1':current_room[1]['var_c1'],'c2':current_room[1]['var_c2'],'start':current_room[1]['running']},room=message['room'])
 
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


@app.route('/user/', methods=['GET', 'POST'])
@app.route('/user/<name>', methods=['GET', 'POST'])
def userstats(name=None):
    return render_template('user.html', name=name)


@app.route('/_time')
def updateTime():
    a = request.args.get('username', 'Konditioner')
    return jsonify(result=read_timer())


@app.route('/_socket', methods=['GET', 'POST'])
def startsocket():
    a = request.args.get('username', 'Konditioner')
    b = request.args.get('BK', 0, type=int)
    c = request.args.get('BT', 1,type=int)
    d = request.args.get('DK', 0,type=int)

    totals = ''
    found = 0
    for x in range(0,len(player_data)):
        if player_data[x][0] == a:
            player_data[x]= [a,b,c,d]
            found = 1
        totals = ''+totals + player_data[x][0] +","+str(player_data[x][1])+","+str(player_data[x][2])+","+str(player_data[x][3])+"$"
    if found == 0:
        player_data.append([a,b,c,d])
        totals = ''+totals + a +","+str(b)+","+str(c)+","+str(d)+"$"

    return jsonify(result=totals)

def get_indicies_from_row(row_name):
	if row_name == "bltr":
		return [4,8,12,16,20]
	if row_name == "tlbr":
		return [0,6,12,18,24]
	if row_name[0:3] == "row":
		row_num = int(row_name[3])
		offset = 5*row_num-5
		return [offset, offset+1, offset+2, offset+3, offset+4]
	if row_name[0:3] == "col":
		col_num = int(row_name[3])
		offset = col_num
		return [offset-1, offset+4, offset+9, offset+14, offset+19]
	else:
		return -1
	


if __name__ == '__main__':
    socketio.run(app)