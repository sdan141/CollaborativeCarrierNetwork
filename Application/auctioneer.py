import time
from carrier_handler import CarrierHandler
from offer import Offer, Auction
import pandas as pd
import utilities as utils
from tabulate import tabulate
import numpy as np



import yaml
import os

script_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
config_path = os.path.join(parent_dir, 'config', 'auctioneer_config.yaml')

# Load the configuration file
with open(config_path, 'r') as config_file:
    config = yaml.safe_load(config_file)

base_timeout = config['constants']['base_timeout']
max_rounds = config['constants']['max_rounds']


# BASE_TIMEOUT = 5
# MAX_ROUNDS = 5

class Auctioneer:
    """
    Class to represent the auctioneer in the transport auction system
    Attributes:
        server_socket (socket.socket): The server socket to listen for connections
        registered_carriers (list)   : List of registered carriers IDs
        offers (dict)                : Key is ID of offer, value is the offer object
        auction_time (float)         : Timestamp for the next phase
        active_carriers (list)       : List of registered carriers IDs which are active
        phase (str)                  : actual auction phase
        next_round (bool)            : If there is another auction round
        _stop_event (threading.Event): force stop all threads
    """
    def __init__(self, socketio):
        self.socketio = socketio
        self.offers = []
        # k,v bundle_Id, list Id offer
        # {1: [0xH54xr,...], 2: [0x15Ftg,...], 3: [0xy56f,...]}
        #self.bundles = [[0,4,2],[6,1,3],[5,7,8]]
        self.registered_carriers = [] 
        self.active_carriers = []
        self.auction_time = None
        self.next_round = True
        self.phase = "REGIST"
        self.bundles = {}
        self.id_on_auction = None
    
    def generate_bundles(self):
        offers_sorted_indices = np.argsort([offer.revenue for offer in self.offers])
        bundle_size = 2
        n = len(self.offers)        
        bundle_iterator = 0

        for i in range(0,int(n/2)):
            if i % bundle_size==0 and i!=0:
                bundle_iterator += 1
                self.bundles[bundle_iterator] = []
               
            if i==0:                
                self.bundles[bundle_iterator] = []

            self.bundles[bundle_iterator].append(self.offers[offers_sorted_indices[i]].offer_id)
            self.bundles[bundle_iterator].append(self.offers[offers_sorted_indices[n-i-1]].offer_id)

        # if i % bundle_size != 0:

    def handle_auction_phases(self):
        while self.next_round:
            if self.auction_time is not None: # at least one registered carrier has sent offers
                for n_round in range(max_rounds):
                    print(f"\nAuction round {n_round+1}/{max_rounds}\n")
                    
                    sold = 0 # for counting how many offers have been sold in the round
                    
                    if not n_round:
                        self._wait_until(self.auction_time)
                        self.generate_bundles()
                        print(f'\nBundles: {self.bundles}\n')

                    self.print_auction_list()
                    for i in range(len(self.offers)): # iterating auction list
                        print(f"\nOffer {i+1}/{len(self.offers)} on sale\n")

                        ######################## need to modify
                        if False:  ### Need somthing like bundle_round to be a boolean veriable or if n_round < x ...
                            for offer in self.offers:
                                if offer.offer_id in self.bundles[self.id_on_auction]:
                                    offer.on_auction = True
                        else:
                            self.offers[i].on_auction = True
                            self.id_on_auction = self.offers[i].offer_id
                        #########################
                             
    
                        self.phase = "REQ_OFFER"
                        print("\nEntering offer request phase")
                        self.socketio.emit('auctioneer_log', {'message': "Entering offer request phase"})
                        self.auction_time = int(time.time()) + base_timeout
                        self._wait_until(self.auction_time)

                        self.phase = "BID"
                        print("\nEntering bidding phase")
                        self.socketio.emit('auctioneer_log', {'message': "Entering bidding phase"})
                        self.auction_time = int(time.time()) + base_timeout
                        self._wait_until(self.auction_time)

                        self.phase = "RESULTS"
                        self.offers[i].update_results()
                        print("\nEntering results phase")
                        self.socketio.emit('auctioneer_log', {'message': "Entering results phase"})
                        self.auction_time = int(time.time()) + base_timeout
                        self._wait_until(self.auction_time)
                        self.check_active_carriers()

                        self.phase = "CONFIRM"
                        print("\nEntering confirmation phase")
                        self.socketio.emit('auctioneer_log', {'message': "Entering confirmation phase"})
                        self.auction_time = int(time.time()) + base_timeout 
                        if self.offers[i].winner != "NONE":
                            sold += 1
                        if i == len(self.offers)-1:
                            # last offer in the leaset on auction
                            if not sold and not self.valide_bids_for_unsold_offer():
                                # no offer was sold and no offer has valide bids
                                self.next_round = False                 
                        self._wait_until(self.auction_time)
                        self.offers[i].on_auction = False

                    self.update_auction_list() 
                    if not self.next_round:
                        print("\nAuction day closed server restarts tomorrow...")
                        self.socketio.emit('auctioneer', {"action": "end"}) # FIXME
                        break
  

    def _wait_until(self, timeout):
        while time.time() < timeout:
            time.sleep(1)
 
    def add_offer(self, carrier_id, offer):
        offer_id = offer['offer_id']
        loc_pickup = offer['loc_pickup']
        loc_dropoff = offer['loc_dropoff']
        min_price = offer['profit']
        revenue = offer['revenue']
        offer = Offer(carrier_id, offer_id, loc_pickup, loc_dropoff, min_price, revenue)
        self.offers.append(offer)
        payload = {
            "carrierId": carrier_id, 
            "offerId": offer_id, 
            "pickup": loc_pickup, 
            "dropoff": loc_dropoff, 
            "minPrice": min_price, 
            "revenue": revenue
        } 
        self.socketio.emit('auctioneer', { "action": "addAuction", "payload": payload })

    def check_active_carriers(self):
        for register in self.registered_carriers:
            if register not in self.active_carriers:
                for offer in self.offers:
                    if offer.on_auction and (register==offer.winner or register==offer.carrier_id):
                        offer.winner = 'NONE'
                        offer.winning_bid = 'NONE'
                        if all([bid < offer.min_price for bid in offer.bids.values()]):
                            offer.bids = {}
        self.registered_carriers = self.active_carriers

    def update_auction_list(self):
        new_list = []
        for offer in self.offers: 
            if offer.winner == "NONE" and offer.carrier_id in self.registered_carriers:
                new_list.append(offer)
        self.offers = new_list

    def print_auction_list(self):
        list_dict =  [utils.flatten_and_round_dict(offer.to_dict()) for offer in self.offers]
        offers_df = pd.DataFrame(list_dict).drop(columns=['offer_id'])
        print(tabulate(offers_df, headers='keys', tablefmt='psql'))


    def valide_bids_for_unsold_offer(self):
        bid_is_legal = []
        for offer in self.offers:
            if offer.winner == "NONE":
                for bid in offer.bids.values():
                    bid_is_legal.append(bid > offer.profit)
        return any(bid_is_legal)
        # in at least one offer that has not been sold there is at least one bid which is legal
        #legal = [bid > offer.profit for bid in offer.bids.values() for offer in self.offers]
