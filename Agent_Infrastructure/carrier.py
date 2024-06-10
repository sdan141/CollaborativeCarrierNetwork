import socket
import json 
import time
import uuid
from cost_model import CostModel
from routing import Routing
import utilities as utils

import numpy as np

class Carrier:

    def __init__(self, carrier_id, socketio=None, server_host=socket.gethostname(), server_port=12349, config_file='config.yaml', deliveries_file='config.yaml'):
        self.carrier_id = carrier_id
        self.server_host = server_host
        self.server_port = server_port
        '''
        self.socketio = socketio
        print(f"Carrier agent {carrier_id} is ready")
        self.socketio.emit(carrier_id, {'message': f"Carrier agent {carrier_id} is ready"})
        '''
        #self.config_file = config_file
        self.cost_model = CostModel(config_file)
        self.routing = Routing(deliveries_file)


    def start(self):
        response = self.register()
        print(json.dumps(response, indent=2, default=str))

        if response['payload']['status'] != 'OK':
            print(response['payload']['status'])
            exit()
        
        self.handle_requests(response)

    def handle_requests(self, response):
        requests_below_thresh_list = utils.get_requests_below_thresh(self.routing.deliveries_df)
        if requests_below_thresh_list:
            for loc_pickup, loc_dropoff, profit, revenue in requests_below_thresh_list:
                response = self.send_offer(loc_pickup, loc_dropoff, profit, revenue) # Send an offer
                #print("\n Auctioneer response to offer:")
                #print(json.dumps(response, indent=2, default=str))
        auction_time = response["timeout"] #if respond["timeout"]!="NONE" else time.time()+30
        time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time

        while True:
            response = self.request_offer() # Request current offers
            print("\n Auctioneer response to request_offers:")
            print(json.dumps(response, indent=2, default=str))

            offer = response["payload"]["offer"]

            ## Calculate bids for each offer and send bid for the most profitable offer

            auction_time = response["timeout"]
            time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time

            ### Calculate a bid for an offer (more than one?)
            ### Should implement start_time/ timeout for fetching offers?

            offer_id = offer['offer_id']
            min_price = offer['min_price']
            revenue = offer['revenue']
            random_bid = np.random.uniform(min_price,revenue-min_price)
            bid = np.random.choise(0, random_bid)

            response = self.send_bid(offer_id, bid)  # Send a bid
            print("\n Auctioneer response to bid:")
            print(json.dumps(response, indent=2, default=str))

            auction_time = response["timeout"]
            time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time

            response = self.request_auction_results()  # Request auction results
            print("\n Auctioneer response to request_results:")
            print(json.dumps(response, indent=2, default=str))

            auction_time = response["timeout"]

            time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time
            
            response = self.confirm_results()
            print("\n Auctioneer response to confirm_results:")
            print(json.dumps(response, indent=2, default=str))
            
            if not response["payload"]["next_round"]:
                print("\nAuction day over")
                exit()

            auction_time = response["timeout"]

            ### Save the relevant results (offer sold/ winning bid)
            time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time


    def connect_to_auctioneer(self):
        carrier_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            carrier_socket.connect((self.server_host, self.server_port))
        except ConnectionRefusedError as e:
            print(f"Error connecting to Auctioneer server: {e}")
            return None
        return carrier_socket

    def send_request(self, action, payload):
        with self.connect_to_auctioneer() as carrier_socket:
            if carrier_socket is None:
                return {"error": "Connection error"}
            request = {
                "carrier_id": self.carrier_id,
                "action": action,
                "time": str(int(time.time())),
                "payload": payload
            }
            carrier_socket.send(json.dumps(request).encode('utf-8'))
            response = carrier_socket.recv(1024)
            try:
                return json.loads(response.decode('utf-8'))
            except json.JSONDecodeError:
                return {"error": "Failed to decode JSON response"}
            
    def register(self):
        return self.send_request("register", {})

    def send_offer(self, loc_pickup, loc_dropoff, profit, revenue):
        offer_id = str(uuid.uuid4())
        payload = {
            "offer_id": offer_id,
            "loc_pickup": loc_pickup,
            "loc_dropoff": loc_dropoff,
            "profit": profit,
            "revenue": revenue
        }
        return self.send_request("offer", payload)

    def request_offer(self):
        return self.send_request("request_offer", {})


    def send_bid(self, offer_id, bid):
        payload = {
            "offer_id": offer_id,
            "bid": bid
        }
        return self.send_request("bid", payload)

    def request_auction_results(self):
        return self.send_request("request_auction_results", {})
    
    def confirm_results(self):
        return self.send_request("confirm", {})