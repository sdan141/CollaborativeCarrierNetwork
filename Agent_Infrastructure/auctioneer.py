import socket
import threading
import json

class Auctioneer:
    def __init__(self, host=socket.gethostname(), port=60000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket type, SOCK_STREAM means a TCP socket
        self.connections = [] # names and adresses of connected carrier agents
        self.rounds = 0

    def start(self):
        self.socket.bind((self.host, self.port)) # bind socket 
        self.socket.listen() # begin listening for incoming connections
        print(f"Auctioneer agent listening on {self.host}:{self.port}")
        
        while True:
            connection, address = self.socket.accept()
            print(f'Accepted connection from {address}')
            carrier_handler = threading.Thread(target=self.handle_carrier, args=(connection,))
            # for each new carrier, a new thread is spawned to handle communication.
            carrier_handler.start()    

    def handle_carrier(self, connection_socket):
        print(f"New connection from {connection_socket.getpeername()}")

        while True:
            try:
                data = connection_socket.recv(1024)
                if not data:
                    break
                ### process incoming data here
                message = data.decode("utf-8") # message is now string
                message = json.loads(message) # message is dictionary
                print(f"Received data from {connection_socket.getpeername()}: {message}")
       
                if message["action"] == "REGISTER" : 
                    # carrier whants to register for auctions -> record and acknoledge

                    self.connections.append((message["name"] ,connection_socket))

                    response = {
                        "action": "ACK",
                        "message": "You are now registered for auctions"
                    }
                    response = json.dumps(response)
                    connection_socket.sendall(bytes(response,"utf-8"))

                elif message["action"] == "TR" :
                    print(f"Received transport request from {message['name']}: {message}")
                    self.start_auction(connection_socket, message)
                    # self.start_auction() or somthing like that
                    #connection_socket.send(bytes(f"Hello {message["name"]} Agent! Your request has bin received","utf-8"))
                    continue
                
                ### send response back to carrier if needed
                ### connection_socket.sendall(response.encode())

            except Exception as e:
                print(f"Error occure during handling connection with carrier {connection_socket.getpeername()}. Error : {e}")
                break

        print(f"Connection from carrier {connection_socket.getpeername()} closed")
        connection_socket.close()

    def send_message(self, connection, message):
        connection.sendall(bytes(message,encoding="utf-8"))
        ### eventually send pickle or json files

    def get_TR_from_carrier(self, connection):
        message = {"action": "REQUEST_TR"}
        message = json.dumps(message)
        self.send_message(connection, message)
        print(f"Sent request to {connection.getpeername()} for transport request for auction")

    def start_auction(self, connection, message):
        print("Starting auction for transport request:", message)
        carrier_name = message["name"]

        del message["action"]
        del message["name"]
        auction_message = {
            "action": "AUCTION",
            **message  
        }
        auction_message = json.dumps(auction_message)
        for name, conn in self.connections:
            if name != carrier_name:
                self.send_message(conn, auction_message)