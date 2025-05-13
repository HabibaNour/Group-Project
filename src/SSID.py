#Some of this code was adapted from the following sources:
#https://thepythoncode.com/article/building-wifi-scanner-in-python-scapy
#https://socket.io/docs/v3/emitting-events/
#https://thepacketgeek.com/scapy/building-network-tools/

from scapy.all import *
from scapy.all import Dot11Beacon, Dot11Elt, Dot11
import os
import time
from threading import Thread, Event
from flask import Flask
from flask_socketio import SocketIO


class selecting_SSID:
    def __init__(self, socketio):
        self.socketio = socketio
        self.seen_networks = {}
        self.selected_ssid = None 
        self.sniff_thread = None
        self.channel_thread = None
        self.stop_event = Event() 

    def change_channel(self):
        channels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140] #excluding 149-165 as not public use normally
        while not self.stop_event.is_set():
            for ch in channels:
                os.system(f"iwconfig wlan0mon channel {ch} >/dev/null 2>&1")
                time.sleep(1)

                if self.stop_event.is_set():
                    break

    def packet_handler(self, packet):
        if packet.haslayer(Dot11Beacon):
            ssid = packet[Dot11Elt].info.decode().strip()
            bssid = packet[Dot11].addr2

            if ssid: #checks if null
                if ssid not in self.seen_networks:
                    self.seen_networks[ssid] = set()
                    stats = packet[Dot11Beacon].network_stats()
                    crypto = ", ".join(stats.get("crypto"))
                    channel = stats.get("channel")

                    #sends to web server, event name + data
                    self.socketio.emit('network_info', {'ssid': ssid,'bssid' : bssid, 'crypto': crypto, 'channel': channel})

                if bssid not in self.seen_networks[ssid]:
                    self.seen_networks[ssid].add(bssid)#fixes duplicate issues

    def start_sniffing(self):
        while not self.stop_event.is_set():
            sniff(iface = 'wlan0mon', prn = self.packet_handler, store = 0, timeout = 2)

    def start_SSID_selection(self):
        self.stop_event.clear()
        Thread(target=self.change_channel, daemon=True).start()
        Thread(target=self.start_sniffing, daemon=True).start()

    def stop_SSID_selection(self):
        self.stop_event.set()

