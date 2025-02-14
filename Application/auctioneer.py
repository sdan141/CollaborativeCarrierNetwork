import time
from offer import Offer
import utilities as utils
import numpy as np

# Needed? FIXME
import pandas as pd
from tabulate import tabulate

import yaml
import os

script_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
config_path = os.path.join(parent_dir, 'config', 'auctioneer_config.yaml')

with open(config_path, 'r') as config_file:
    config = yaml.safe_load(config_file)

base_timeout = config['constants']['base_timeout']
max_rounds = config['constants']['max_rounds']

BUNDLE_ROUNDS = 2


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
        self.registered_carriers = [] 
        self.active_carriers = []
        self.auction_time = None
        self.next_round = True
        self.phase = "REGIST"
        self.bundles = {}
        self.id_on_auction = None
        self.indices_on_auction = []
    
     
    def generate_bundles(self, bundle_size=2):
        offers_sorted_indices = np.argsort([offer.revenue for offer in self.offers])
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

        if n % 2:
            # if n is not even middle element has its own bundle
            bundle_iterator += 1
            self.bundles[bundle_iterator] = []
            self.bundles[bundle_iterator].append(self.offers[offers_sorted_indices[int(n/2)]].offer_id)

        # Emit bundles
        for i in range(0, len(self.bundles)):
            print(f"Sending bundle {i}: {self.bundles[i]}")
            self.socketio.emit('auctioneer', {'payload': self.bundles[i], 'action': 'addBundle'})
        
        # Emit offers
        for i in range(0, n):
            self.socketio.emit('auctioneer', {'payload': {
                                                "carrierId": self.offers[i].carrier_id,
                                                "offerId": self.offers[i].offer_id,
                                                "pickup": self.offers[i].loc_pickup,
                                                "dropoff": self.offers[i].loc_dropoff,
                                                "revenue": self.offers[i].revenue,
                                                "minPrice": self.offers[i].min_price
                                                }, 
                                            "action": 'addAuction'})

        for k, v in self.bundles.items():
            if not v:
                print(f"\nBundle {k} is empty!\n") 


    def handle_auction_phases(self):
        start_time_auction_day = time.time()
        while self.next_round:
            if self.auction_time is not None: # at least one registered carrier has sent offers
                n_round = 0
                while n_round < max_rounds:
                    print(f"\nAuction round {n_round+1}/{max_rounds}\n")
                    # self.socketio.emit('auctioneer_log', {'message': f"Auction round {n_round+1}/{max_rounds}"}) FIXME
                    sold = 0 # for counting how many offers have been sold in the round
                    
                    if n_round == 0:
                        # This is the 1.st round
                        self._wait_until(self.auction_time)
                        self.generate_bundles()
                    self.print_auction_list()

                    if n_round < BUNDLE_ROUNDS: #bundle round
                        for current_bundle in range(len(self.bundles)): # iterating through bundle list
                            print(f"\n Bundle on auction:{current_bundle+1}/{len(self.bundles)}\n")
                            self.socketio.emit('auctioneer_log', {'message': f"Bundle on auction:{current_bundle+1}/{len(self.bundles)}"})
                            # (Shachar:) converting current bundle list to set cause its faster (O(1) instead of O(n))
                            current_bundle_set = set(self.bundles[current_bundle])
                            self.indices_on_auction = [i for i, offer in enumerate(self.offers) if offer.offer_id in current_bundle_set]
                            # Set bundles on offer
                            if not self.indices_on_auction:
                                continue
                            print("\n Incides on auction: ", self.indices_on_auction)
                            for j in self.indices_on_auction:
                                self.offers[j].on_auction = True
                            # Set Auction ID to first offer of bundle (eg. "bundle_firstofferid")
                            self.id_on_auction = "bundle_" + str(self.bundles[current_bundle][0]) # FIXME: ACCESS first element of bundle

                            self.phase = "REQ_OFFER"
                            self.auction_time = int(time.time()) + base_timeout
                            print("\nEntering offer request phase")
                            self.socketio.emit('auctioneer_log', {'message': "Entering offer request phase"})
                            self._wait_until(self.auction_time)

                            self.phase = "BID"
                            self.auction_time = int(time.time()) + base_timeout
                            print("\nEntering bidding phase")
                            self.socketio.emit('auctioneer_log', {'message': "Entering bidding phase"})
                            self._wait_until(self.auction_time)

                            self.phase = "RESULTS"
                            self.auction_time = int(time.time()) + base_timeout
                            print("\nEntering results phase")
                            self.socketio.emit('auctioneer_log', {'message': "Entering results phase"})
                            # Update Multi Offer
                            for j in self.indices_on_auction:
                                self.offers[j].update_results()
                            ########################################
                            offers_on_auction = []
                            for i in self.indices_on_auction:
                                    offers_on_auction.append(self.offers[i])
                            payload = {
                                "status": "OK",
                                "offers": [ob.to_dict() for ob in offers_on_auction]
                            }
                            self.socketio.emit('auctioneer', { "payload": payload, "action": "addResult", "round": "bundle"})  
                            ##########################################
                            self._wait_until(self.auction_time)
                            # Check if all registered carriers are active
                            self.check_active_carriers()

                            self.phase = "CONFIRM"
                            print("\nEntering confirmation phase")
                            self.socketio.emit('auctioneer_log', {'message': "Entering confirmation phase"})
                            self.auction_time = int(time.time()) + base_timeout 
                            
                            # Stats for Multi Offer
                            for j in self.indices_on_auction:
                                if self.offers[j].winner != "NONE":
                                    sold += 1

                            #FIXME: later, because I am not sure if this is relevant at this point (maybe if there are only bundles)
                            #(Shachar:) what if all bundles are sold? Idea: check if bundle list hasn't changed 
                            # -> if so need to jump to single auctions or change bundle distribution
                            # also need to check if all were sold -> no next round!

                            if current_bundle == len(self.bundles)-1:
                                if not sold and not self.valide_bids_for_unsold_offer():
                                    n_round = BUNDLE_ROUNDS-1
                                    self._wait_until(self.auction_time)
                                    continue
                                    # continue with single auctions
                            if sold == len(self.offers):
                                self.next_round = False
                            self._wait_until(self.auction_time)
                            # Set Multiple Offers to on_auction = False
                            for j in self.indices_on_auction:
                                self.offers[j].on_auction = False
                            self.indices_on_auction = []
                    
                    else: #single offer Round
                        print("\nSelling individual offers!!!\n")
                        self.socketio.emit('auctioneer_log', {'message': "Selling individual offers!"})
                        for i in range(len(self.offers)): # iterating auction list print(f"\nOffer {i+1}/{len(self.offers)} on sale\n")
                            print(f"\nOffer on auction:{i+1}/{len(self.offers)}\n")

                            ######################## need to modify
                            if False:  ### Need somthing like bundle_round to be a boolean veriable or if n_round < x ...
                                for offer in self.offers:
                                    if offer.offer_id in self.bundles[self.id_on_auction]:
                                        offer.on_auction = True
                            else:
                                self.offers[i].on_auction = True
                                self.id_on_auction = self.offers[i].offer_id
                                self.indices_on_auction = [i]
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
                            ########################################
                            offers_on_auction = []
                            for i in self.indices_on_auction:
                                    offers_on_auction.append(self.offers[i])
                            payload = {
                                "status": "OK",
                                "offers": [ob.to_dict() for ob in offers_on_auction]
                            }
                            self.socketio.emit('auctioneer', { "payload": payload, "action": "addResult", "round": "single"})  
                            ##########################################
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
                            if sold == len(self.offers):
                                self.next_round = False               
                            self._wait_until(self.auction_time)
                            self.offers[i].on_auction = False
                    self.update_auction_list() 

                    if not self.next_round:
                        if self.offers:
                            self.print_auction_list() 
                        print("\nAuction day closed server restarts tomorrow...")
                        print(f"Total duration of today's auction: {(time.time()-start_time_auction_day)/60}\n")
                        self.socketio.emit('auctioneer', {"action": "stopServer"})
                        exit()
                    n_round += 1


    def _wait_until(self, timeout):
        while time.time() < timeout:
            time.sleep(1)
 
    def add_offer(self, carrier_id, offer):
        offer_id = offer['offer_id']
        loc_pickup = offer['loc_pickup']
        loc_dropoff = offer['loc_dropoff']
        min_price = offer['profit']
        revenue = offer['revenue']
        offer = Offer(carrier_id, offer_id, loc_pickup, loc_dropoff, revenue, min_price)
        self.offers.append(offer)

    def check_active_carriers(self):
        for register in self.registered_carriers:
            if register not in self.active_carriers:
                for i in self.indices_on_auction:
                    offer = self.offers[i]
                    if register==offer.winner or register==offer.carrier_id:
                        offer.winner = 'NONE'
                        offer.winning_bid = 'NONE'
                        if all([bid < offer.min_price for bid in offer.bids.values()]):
                            offer.bids = {}
        self.registered_carriers = self.active_carriers

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
        list_dict = [offer.to_dict() for offer in self.offers]
        utils.print_offer_list(list_dict)

    def valide_bids_for_unsold_offer(self):
        bid_is_legal = []
        for offer in self.offers:
            if offer.winner == "NONE":
                for bid in offer.bids.values():
                    bid_is_legal.append(bid > offer.min_price)
        return any(bid_is_legal)
    
    def calculate_share(self, single_offer_id, bid):
        # Calculate all_cost and get revenue for single_offer_id
        all_cost = 0
        single_revenue = 0
        #(Shachar:) filters the offers in a single pass, which is typically faster than filtering in a for loop
        bundle_offers = [self.offers[i] for i in self.indices_on_auction]
        all_cost = sum(offer.revenue for offer in bundle_offers)
        single_revenue = next(offer.revenue for offer in bundle_offers if offer.offer_id == single_offer_id)
        share = (single_revenue / all_cost) * bid
        return share

    


