#Some of this code was adapted from the following places:
#https://github.com/SiliconDojo/Online-Classes/blob/main/Coding%20DIY%20-%20Build%20Network%20Monitoring%20Web%20Apps/Coding%20DIY%20-%20Build%20Network%20Monitoring%20Web%20Apps%20-%20Lab%20Book.pdf
#https://docs.python.org/3/library/csv.html
#https://socket.io/docs/v3/emitting-events/
#https://thepacketgeek.com/scapy/building-network-tools/
#https://stackoverflow.com/questions/60612283/how-to-capture-airodump-ng-scan-output-to-csv-that-mirrors-the-output-shown-in-t

from scapy.all import *
import os
import time
from threading import Thread
from flask import Flask
from flask_socketio import SocketIO
import csv
import requests
from datetime import datetime

class devices:
    def __init__(self, socketio):
        self.socketio = socketio #prevents global sockets so easier for combining with other live updating
        self.seen_macs = set() 
        self.selected_SSID = None
        self.channel = None
        self.selected_MAC = None
        self.handle_socket()
        self.current_time = datetime.now()

    def handle_socket(self):
        @self.socketio.on('home_SSID') 
        def home_SSID_handler(data):
            self.selected_SSID = data['ssid']
            self.channel = data['channel']
            self.selected_MAC = data['bssid']
            
            Thread(target = self.run_airodump, daemon = True).start()
            Thread(target = self.read_csv, daemon = True).start()

    def run_airodump(self):
        for file in os.listdir(): #removes previous file
            if file.startswith("macaddresses-") and file.endswith(".csv"):
                os.remove(file)

        command = f"sudo airodump-ng wlan0mon --channel {self.channel} --essid '{self.selected_SSID}' --write macaddresses --output-format csv >/dev/null 2>&1"
        os.system(command)

    def get_vendor_from_api(self, mac):
        try:
            url = f"https://api.macvendors.com/{mac}"
            response = requests.get(url, timeout = 5)
            if response.status_code == 200:
                return response.text
            else:
                return "Unknown vendor"
            
        except Exception as e:
            print(f"Vendor lookup failed for {mac}: {e}")
            return "Error: Unknown vendor"

    def read_csv(self):
        csv_file = "macaddresses-01.csv"

        timeout = 30 #might fix crashing?
        start_time = time.time()

        while not os.path.exists(csv_file):
            if time.time() - start_time > timeout: #continuing may fix crashing
                return
            time.sleep(1)

        while True:
            try:
                with open(csv_file, mode = 'r', encoding = 'utf-8', errors = 'ignore') as file:
                    csv_reader = csv.reader(file)
                    bottom_of_file = False

                    for row in csv_reader:
                        if not bottom_of_file and row and row[0].strip() == "Station MAC":
                                bottom_of_file = True
                                continue

                        if bottom_of_file and row and len(row) > 0:
                            mac = row[0].strip()
                            bssid = row[5].strip()

                            if mac and mac.count(":") == 5 and mac not in self.seen_macs and self.selected_MAC == bssid.lower():
                                self.seen_macs.add(mac)

                                vendor = self.get_vendor_from_api(mac)

                                print(f"New MAC: {mac} and {vendor}")
                                self.socketio.emit('new_mac', {'mac' : mac, 'vendor' : vendor, 'timestamp' : self.current_time.strftime('%c')})

            except Exception as e:
                print("Error reading CSV:", e)

            time.sleep(2)
   
