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
        print(f"\nAuctioneer agent listening on {self.host}:{self.port}\n")
        
        while True:
            connection, address = self.socket.accept()
            print(f'\nAccepted connection from: {address}\n')
            carrier_handler = threading.Thread(target=self.handle_carrier, args=(connection,))
            # for each new carrier, a new thread is spawned to handle communication.
            carrier_handler.start()    

    def handle_carrier(self, connection_socket):
        print(f"\nNew connection from {connection_socket.getpeername()}\n")

        while True:
            try:
                data = connection_socket.recv(1024)
                if not data:
                    break
                ### process incoming data here
                message = data.decode("utf-8") # message is now string
                message = json.loads(message) # message is dictionary
                print(f"\nReceived data from {connection_socket.getpeername()}: \n{message}\n")
       
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
                    print(f"\nReceived transport request from Agent {message['name']}: \n{message}\n")
                    self.start_auction(connection_socket, message)
                    # self.start_auction() or somthing like that
                    #connection_socket.send(bytes(f"Hello {message["name"]} Agent! Your request has bin received","utf-8"))
                    continue
                
                ### send response back to carrier if needed
                ### connection_socket.sendall(response.encode())

            except Exception as e:
                print(f"\nError occure during handling connection with carrier {connection_socket.getpeername()}. \nError : {e}\n")
                break

        print(f"\nConnection from carrier {connection_socket.getpeername()} closed\n")
        connection_socket.close()

    def send_message(self, connection, message):
        connection.sendall(bytes(message,encoding="utf-8"))
        ### eventually send pickle or json files

    def get_TR_from_carrier(self, connection):
        message = {"action": "REQUEST_TR"}
        message = json.dumps(message)
        self.send_message(connection, message)
        print(f"\nSent request to {connection.getpeername()} for transport request for auction\n")

    def start_auction(self, connection, message):
        print(f"\nStarting auction for transport request:\n{message}\n")
        carrier_name = message["name"]

        del message["action"]
        del message["name"]
        message["min_price"] = message.pop("profit")
        auction_message = {
            "action": "AUCTION",
            **message  
        }
        auction_message = json.dumps(auction_message)
        for name, conn in self.connections:
            if name != carrier_name:
                self.send_message(conn, auction_message)