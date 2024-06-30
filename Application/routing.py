# imports...
import yaml
from algorithm import AlgorithmBase
import utilities as utils
from cost_model import CostModel
from offer import Offer
import uuid
import numpy as np

from tabulate import tabulate # FIXME

class Routing(AlgorithmBase):

    def __init__(self, carrier_id, socketio, dt_data, depot, cost_model):
        self.carrier_id = carrier_id
        self.socketio = socketio
        self.cost_model = CostModel(cost_model)
        self.offers = self.create_offer_list(dt_data)
        self.depot_location = depot
        self.on_auction_indices = []
        locations, assignmets = self.get_locations_and_assignmets()
        print(f"\nCreated locations: {[(round(ll,2),round(lr,2)) for ll, lr in locations]} \nand assignments: {assignmets}\n")

        super().__init__(locations, assignmets)
        

    def create_offer_list(self, dt_data):
        offers = []
        for i, offer in dt_data.iterrows():
            offer_id = str(uuid.uuid4())
            loc_pickup = {
                "pos_x": offer.pickup_long, 
                "pos_y": offer.pickup_lat
                }
            loc_dropoff = {
                "pos_x": offer.delivery_long, 
                "pos_y": offer.delivery_lat
                }
            revenue = offer.revenue
            profit = offer.profit
            offers.append(Offer(self.carrier_id, offer_id, loc_pickup, loc_dropoff, revenue, profit))
        return offers

    def set_depot_location(self, config_file):
        if not config_file:
            loc = (np.random.uniform(-100,100), np.random.uniform(-100,100)) 
        else:
            with open(config_file, 'rb') as stream:
                try:
                    data_loaded = yaml.safe_load(stream)
                    loc = data_loaded['depote_location']
                except yaml.YAMLError as e:
                    print(e)
        return loc
    
    def get_locations_and_assignmets(self): 
        locations = [self.depot_location]
        assignments = []
        for offer in self.offers:
            if offer.winner == "NONE" or offer.winner == self.carrier_id : # interested only in transport requests that were not sold
                # Extract positions and append to locations
                pickup_index = len(locations)  # Index of the next pickup location
                locations.append((offer.loc_pickup["pos_x"], offer.loc_pickup["pos_y"]))
                
                dropoff_index = len(locations)  # Index of the next dropoff location
                locations.append((offer.loc_dropoff["pos_x"], offer.loc_dropoff["pos_y"]))
                
                # Append the indices to the assignment list
                assignments.append([pickup_index, dropoff_index])
        return locations, assignments
    

    def get_offers_on_auction(self):
        on_auction_indices = []
        for i, offer in enumerate(self.offers):
            if offer.on_auction:
                on_auction_indices.append(i)
        return on_auction_indices
    

    def get_requests_below_threshold(self):
        requests_below_thresh = []
        print()
        for i, offer in enumerate(self.offers):
            if offer.profit < float(self.cost_model.sell_threshhold):
                self.socketio.emit(self.carrier_id, {'message': f"Sendin offer with profit: {offer.profit}€!", "action": "log"})
                offer.on_auction = True
                requests_below_thresh.append(offer)
                self.on_auction_indices.append(i)
        print(requests_below_thresh)
        return requests_below_thresh


    def calculate_bid(self, loc_pickup, loc_dropoff, revenue):
        # optimal_tour_distance = float(self.optimal_tour['distance'])
        # optimal_tour_with_offer_distance = float(self.get_optimal_tour(ignore_indices=self.on_auction_indices,\
        #                                            include_pickups=loc_pickup, include_dropoffs=loc_dropoff)['distance'])
        # margin_distance = optimal_tour_with_offer_distance - optimal_tour_distance
        # margin_cost = self.cost_model.get_marginal_cost(margin_distance)
        # bid = revenue - margin_cost - self.cost_model.buy_threshold
        # if bid < minimum_price:
        #     bid  = 0
        return 190


    def update_offer_list(self, offer_to_update):
        if self.carrier_id==offer_to_update['offeror']:
            # carrier is the offeror and maybe the winner
            for offer in self.offers:
                if offer_to_update['offer_id']==offer.offer_id:
                    offer.winner = offer_to_update['winner']
                    offer.winning_bid = offer_to_update['winning_bid']
        else:                  
            # carrier is the winner but not the offeror          
            self.offers.append(self.add_offer(offer_to_update)) 

    def add_offer(self, offer):
        carrier_id = offer['offeror']
        offer_id = offer['offer_id']
        loc_pickup = offer['loc_pickup']
        loc_dropoff = offer['loc_dropoff']
        profit = loc_pickup, loc_dropoff
        revenue = offer['revenue']
        return Offer(carrier_id, offer_id, loc_pickup, loc_dropoff, profit, revenue) # offer.on_auction = False by default
        


