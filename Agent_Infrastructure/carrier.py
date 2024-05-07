import socket
import json
import pandas as pd
from tabulate import tabulate

class Carrier:
    def __init__(self, name, host=socket.gethostname(), port=2000):
        self.host = host
        self.port = port
        self.name = name
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # SOCK_STREAM means a TCP socket
    
    def connect(self, server_host, server_port):
        self.socket.connect((server_host, server_port))
        print(f"\nConnected to Auctioneer agent on {server_host}:{server_port}\n")
 
    def send_message(self, message):
        self.socket.sendall(bytes(message,encoding="utf-8"))
        ### eventually send pickle or json files

    def receive_message(self):
        received = self.socket.recv(1024)
        received = received.decode("utf-8")
        received = json.loads(received)
        return received
    
    def start(self):
        while True:
            try:
                data = self.socket.recv(1024)
                if data:
                    message = json.loads(data.decode("utf-8"))
                    self.handle_message(message)
                    
            except Exception as e:
                print(f"\nError occurred during message reception: {e}\n")    

    def handle_message(self, message):
        if message["action"] == "ACK": 
            print(f"\nReceived message: \n{message['message']}\n")

        elif message["action"] == "REQUEST_TR":
            print("\nReceived request for transport point\n")
            response = self.send_transport_point()
            self.send_message(json.dumps(response))

        elif message["action"] == "AUCTION":
            print(f"\nReceived auction message for transport request: \n{message}\n")
            self.handle_auction(message)

    def send_transport_point(self):
        deliveries_df = pd.read_csv("example_TR.csv")
        print(f"\nAll deliveries: \n")
        print(tabulate(deliveries_df, headers='keys', tablefmt='psql'))
        below_threshold = deliveries_df[(deliveries_df.profit).astype(float)<100]
        print(f"\n\ndeliveries below threshhold: \n")
        print(tabulate(below_threshold, headers='keys', tablefmt='psql'))
        if len(below_threshold) > 0:
            delivery_point = below_threshold.iloc[0].to_dict()
            data = {
                "action"        : "TR", 
                "name"          : self.name, 
                **delivery_point
            }

        else:
            data =   {
                "action" : "NO_TR", 
                "name"   : self.name
            }
        print(f"\n\nTransport request to send: \n{data}\n")
        return data 
    
    def handle_auction(self, auction_message):
        del auction_message["action"]
        bid = self.evaluate_transport_request(auction_message)
        self.send_bid(bid)

    def evaluate_transport_request(self, transport_request):
        with open('transport_request.json', 'w') as f:
            json.dump(transport_request, f)
        bid = input("how much are you ready to pay for this TR?\t")
        ### evaluate the transport request in the application
        # calculate marginal profit
        # decide bid value
        return bid

    def send_bid(self, bid_price):
        message = {
            "action": "BID",
            "name": self.name,
            "bid_price": bid_price
        }
        self.send_message(json.dumps(message))

    def disconnect(self):
        self.socket.close()
        print("Disconnected from Auctioneer agent")

### For better organization: Create seperate file with all message types 
### and a function that organizes them