import socket
import json

class Carrier:
    def __init__(self, name, host=socket.gethostname(), port=2000):
        self.host = host
        self.port = port
        self.name = name
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # SOCK_STREAM means a TCP socket
    
    def connect(self, server_host, server_port):
        self.socket.connect((server_host, server_port))
        print(f"Connected to Auctioneer agent on {server_host}:{server_port}")
 
    def send_message(self, message):
        self.socket.sendall(bytes(message,encoding="utf-8"))
        ### eventually send pickle or json files

    def receive_message(self):
        received = self.socket.recv(1024)
        received = received.decode("utf-8")
        received = json.loads(received)
        return received
    
    def disconnect(self):
        self.socket.close()
        print("Disconnected from Auctioneer agent")