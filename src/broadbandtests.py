import speedtest
import threading
from flask_socketio import SocketIO

class bandwidth_tests:
    def __init__(self, socketio):
        self.socketio = socketio #prevents global sockets so easier for combining with other live updating
        self.running = False
        self.thread = None  #stores thread

    def broadband_tests(self):
        while self.running:
            test = speedtest.Speedtest(secure=True) #runs through HTTPS

            download_speed = test.download() / 1000000 #convert to Mbps
            upload_speed = test.upload() / 1000000 #convert to Mbps

            test.get_best_server()
            ping = test.results.ping

            #sends to web server, event name + data
            self.socketio.emit('speedtest_results', {'download': round(download_speed, 2),
                                                'upload': round(upload_speed, 2),
                                                'ping': round(ping, 2)})

            self.socketio.sleep(5) #run speed test every 5 seconds


    def start_speedtests(self):
        if not self.running:
            self.running = True #starts threading
            self.thread = threading.Thread(target = self.broadband_tests) #creates thread
            self.thread.daemon = True #enables daemon thread
            self.thread.start() #start