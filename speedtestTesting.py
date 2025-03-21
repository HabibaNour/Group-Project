import speedtest
import threading
from flask_socketio import SocketIO
from flask import Flask, render_template, request

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def broadband_tests():
    while True:
        test = speedtest.Speedtest(secure=True)#runs through https

        download_speed = test.download() / 1000000  #converts to Mbps
        upload_speed = test.upload() / 1000000  #converts to Mbps

        test.get_best_server()
        ping = test.results.ping

        #sends to web server, event name + data
        socketio.emit('speedtest_results', {'download': round(download_speed, 2),
                                            'upload': round(upload_speed, 2),
                                            'ping': round(ping, 2)})

        socketio.sleep(15) #run speed test every 15 seconds

speedtests_thread = threading.Thread(target=broadband_tests)
speedtests_thread.daemon = True
speedtests_thread.start()

@app.route('/')
def index():
    return render_template('broadband.html')

if __name__ == '__main__':
    socketio.run(app)
