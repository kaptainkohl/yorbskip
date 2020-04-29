from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!?'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('BattleBingo.html')
    
@app.route('/BattleBingo')
def battle():
    return render_template('BattleBingo.html')    

@socketio.on('my event')
def test_message(message):
    print('received message: ' + message)
    
@socketio.on('clicked')
def handle_array(data):
    print(data)
    emit("newdata", data , broadcast=True)
    
@socketio.on('start')
def handle_start(data):
    emit("startgame", data , broadcast=True)   


if __name__ == '__main__':
    socketio.run(app)