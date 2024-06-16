import socket
import json 
import time
from routing import Routing
import utilities as utils
from requests_handler import RequestHandler

import numpy as np

class Carrier:

    def __init__(self, carrier_id, socketio=None, server_host=socket.gethostname(), server_port=12351, path_config='config.yaml', path_deliveries='config.yaml'):
        self.carrier_id = carrier_id
        '''
        self.socketio = socketio
        print(f"Carrier agent {carrier_id} is ready")
        self.socketio.emit(carrier_id, {'message': f"Carrier agent {carrier_id} is ready"})
        '''
        #self.config_file = config_file
        self.routing = Routing(carrier_id, path_config, path_deliveries)
        self.request_handler = RequestHandler(carrier_id, server_host, server_port)


    def _wait_until(self, timeout):
        while time.time() < timeout:
            time.sleep(1)

    def calculate_bid(self, offer, randomized=False):
        offer_id = offer['offer_id']
        revenue = float(offer['revenue'])
        if randomized:
            random_bid = np.random.uniform(100,revenue-150)
            bid = np.random.choice([0, random_bid])
        else:
            loc_pickup = utils.dict_to_float(offer['loc_pickup']).values()
            loc_dropoff = utils.dict_to_float(offer['loc_dropoff']).values()
            bid = self.routing.calculate_bid(tuple(loc_pickup), tuple(loc_dropoff), revenue)
        return offer_id, bid
    
    def update_offer_list(self, offer):
        if offer['offeror']==self.carrier_id or offer['winner']==self.carrier_id:
            self.routing.update_offer_list(offer)

    def start(self):
        # perform registration
        response = self.request_handler.register()
        if not response or 'payload' not in response or response['payload']['status'] != 'OK':
            print("Registration failed:", response)
            exit()

        # perform sending offers below threshold
        requests_below_thresh_list = self.routing.get_requests_below_threshold()
        if requests_below_thresh_list:
            for offer in requests_below_thresh_list:
                response = self.request_handler.send_offer(offer) # Send an offer

        auction_time = response["timeout"] #if respond["timeout"]!="NONE" else time.time()+30
        self._wait_until(auction_time+2)  # Wait to auction time

        while True:
            # perform request offer
            response = self.request_handler.request_offer() # Request current offers
            print("\n Auctioneer response to request_offers:")
            print(json.dumps(response, indent=2, default=str))

            offer = response["payload"]["offer"]
            offer_id, bid = self.calculate_bid(offer)
            
            auction_time = response["timeout"]
            self._wait_until(auction_time+2)  # Wait to auction time

            # perform bidding
            response = self.request_handler.send_bid(offer_id, bid)  # Send a bid
            print("\n Auctioneer response to bid:")
            print(json.dumps(response, indent=2, default=str))

            auction_time = response["timeout"]
            self._wait_until(auction_time+2)  # Wait to auction time

            # perform request auction results
            response = self.request_handler.request_auction_results()  # Request auction results
            print("\n Auctioneer response to request_results:")
            print(json.dumps(response, indent=2, default=str))

            auction_time = response["timeout"]
            self._wait_until(auction_time+2)  # Wait to auction time

            # perform request results confirmation and next round
            response = self.request_handler.confirm_results()
            print("\n Auctioneer response to confirm_results:")
            print(json.dumps(response, indent=2, default=str))

            offer = response["payload"]["offer"]
            self.update_offer_list(offer) # Save the relevant results (offer sold/ winning bid)
            
            if not response["payload"]["next_round"]:

                #### see which offers were not sold, calculate final profit, compare profits
            
                print("\nAuction day over")
                exit()

            auction_time = response["timeout"]
            self._wait_until(auction_time+2)
