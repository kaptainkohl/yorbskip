from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!?'
socketio = SocketIO(app)

var_seed = 0
var_player1 = []
var_player2 = []

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/BattleBingo')
def battle():
    return render_template('BattleBingo.html')  

@app.route('/BingoStats')
def stats():
    return render_template('BingoStats.html')

@app.route('/HorizontalGoals')
def horGoals():
    return render_template('HorizontalGoals.html')     

@socketio.on('my event')
def test_message(message):
    print(var_seed)
    emit("load", {'seed': var_seed, 'player1':var_player1,'player2':var_player2}, broadcast=True);
    
@socketio.on('clicked')
def handle_array(data):
    global var_player1
    global var_player2
    var_player1 = data['p1']
    var_player2 = data['p2']
    emit("newdata", data , broadcast=True)
    
@socketio.on('start')
def handle_start(msg):
    global var_seed
    print(msg)
    print(msg['data'])
    var_seed = msg['data']
    emit("startgame", msg , broadcast=True)   


if __name__ == '__main__':
    socketio.run(app)