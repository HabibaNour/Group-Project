from flask import Flask, render_template
from flask_socketio import SocketIO
from src.broadbandtests import bandwidth_tests #imports class

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

#starts the tests when the app starts
speed_test = bandwidth_tests(socketio) #creates object passing socketio through
speed_test.start_speedtests()

@app.route('/')
def index():
    return render_template('broadband.html')

if __name__ == '__main__':
    socketio.run(app)
