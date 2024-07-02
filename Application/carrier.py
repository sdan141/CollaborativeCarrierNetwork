import socket
import json 
import time
from routing import Routing
import utilities as utils
from requests_handler import RequestHandler

import numpy as np
from tabulate import tabulate
import pandas as pd

class Carrier:

    def __init__(self, carrier_id, socketio, dt_data, depot, cost_model, server_host=socket.gethostname(), server_port=12350):
        self.carrier_id = carrier_id
        self.socketio = socketio
        print(f"\nCarrier agent {carrier_id} is ready")
        self.socketio.emit(carrier_id, {'message': f"Carrier agent {carrier_id} is ready", "action": "log"})
        self.routing = Routing(carrier_id, socketio, dt_data, depot, cost_model)
        print("\nTransport requests:") # FIXME
        self.print_offer_list()  # FIXME
        self.request_handler = RequestHandler(carrier_id, socketio, server_host, server_port)


    def _wait_until(self, timeout):
        while time.time() < timeout:
            time.sleep(1)

    def calculate_bid(self, offer):
        offer_id = offer['offer_id']
        revenue = float(offer['revenue'])
        # offer['loc_pickup'] = [{'pos_x': ..., 'pos_y': ...}, {'pos_x': ..., 'pos_y': ...}]
        loc_pickup = []
        loc_dropoff = []
        for i in range(len(offer['loc_pickup'])):
            loc_pickup.append(tuple(utils.dict_to_float(offer['loc_pickup'][i]).values()))
            loc_dropoff.append(tuple(utils.dict_to_float(offer['loc_dropoff'][i]).values()))
        bid = self.routing.calculate_bid(loc_pickup, loc_dropoff, revenue)
        return offer_id, bid

    def update_offer_list(self, offer):
        if (offer['offeror']==self.carrier_id and offer['winner']!="NONE") or offer['winner']==self.carrier_id :
            self.routing.update_offer_list(offer)


    def start(self):
        # perform registration
        response = self.request_handler.register()
        if not response or 'payload' not in response or response['payload']['status'] != 'OK':
            print("Registration failed:", response)
            self.socketio.emit(self.carrier_id, {'message': f"Registration failed: {response}"})
            exit()
        
        print(f"\nRegistered for auction!\n")
        self.socketio.emit(self.carrier_id, {'message': f"{response['payload']['status']}"})
        # perform sending offers below threshold
        self.socketio.emit(self.carrier_id, {'message': f"Sending offers with profit below {self.routing.cost_model.sell_threshhold}€", "action": "log"})
        requests_below_thresh_list = self.routing.get_requests_below_threshold()
        print(f"\nSending offers with profit below threshold...\n")
        if requests_below_thresh_list:
            for offer in requests_below_thresh_list:
                self.socketio.emit(self.carrier_id, {'message': f"Send offer ({offer.loc_pickup['pos_x']}, {offer.loc_pickup['pos_y']}) -> ({offer.loc_dropoff['pos_x']}, {offer.loc_dropoff['pos_y']}) | Profit: {offer.min_price}", 
                                                     "action": "log"}) 
                response = self.request_handler.send_offer(offer) # Send an offer
        else:
            self.socketio.emit(self.carrier_id, {'message': "No requests below threshold.", "action": "log"})
            print(f'\n No requests below threshold, you are good to go!\n')
            exit()
        auction_time = response["timeout"]
        self._wait_until(auction_time+1)  # Wait to auction time

        while True:
            # perform request offer
            response = self.request_handler.request_offer() # Request current offers
            
            print("\n Auctioneer response to request_offers:")
            if response["payload"]["status"]!="OK":
                print(json.dumps(response, indent=2, default=str))
                self.socketio.emit(self.carrier_id, response) 
            else:
                print(json.dumps(response["payload"], indent=2, default=str)) 
                self.socketio.emit(self.carrier_id, response) 
            offer = response["payload"]["offer"]
            offer_id, bid = self.calculate_bid(offer)
            
            auction_time = response["timeout"]
            self._wait_until(auction_time+1)  # Wait to auction time
            # perform bidding
            response = self.request_handler.send_bid(offer_id, bid)  # Send a bid
            print("\n Auctioneer response to bid:")
            if response["payload"]["status"]!="OK":
                print(json.dumps(response, indent=2, default=str))
                self.socketio.emit(self.carrier_id, response) 
            else:
                print(json.dumps(response["payload"], indent=2, default=str)) 
                self.socketio.emit(self.carrier_id, response) 
            auction_time = response["timeout"]
            self._wait_until(auction_time+1)  # Wait to auction time

            # perform request auction results: Receives list of single offers; bundles no longer needed
            response = self.request_handler.request_auction_results()  # Request auction results
            
            print("\n Auctioneer response to request_results:")
            if response["payload"]["status"]!="OK":
                print(json.dumps(response, indent=2, default=str))
                self.socketio.emit(self.carrier_id, response) 
            else:
                print(json.dumps(response["payload"], indent=2, default=str)) 
                self.socketio.emit(self.carrier_id, response) 

            auction_time = response["timeout"]
            self._wait_until(auction_time+1)  # Wait to auction time

            response = self.request_handler.confirm_results()
            print("\n Auctioneer response to confirm_results:")
            print(json.dumps(response["payload"], indent=2, default=str))
            self.socketio.emit(self.carrier_id, response) 
            # payload: [offer1, offer2, ...]
            received_offers = response["payload"]["offers"]
            for received_offer in received_offers:
                self.update_offer_list(received_offer)              

            if not response["payload"]["next_round"]:
                self.routing.update_statistics()
                self.print_offer_list()
                print("\nAuction day over")
                ######################################################### Do the plot and data send  FIXME
                offers_list = [offer.to_dict() for offer in self.routing.offers]
                offers_json = json.dumps(offers_list)
                self.socketio.emit(self.carrier_id, {'message': "The auction is over!", 'payload': offers_json, "action": "end"})
                #########################################################
                exit()

            auction_time = response["timeout"]
            self._wait_until(auction_time+1)


    def print_offer_list(self):
        list_dict = [offer.to_dict() for offer in self.routing.offers]
        utils.print_offer_list(list_dict)

        
