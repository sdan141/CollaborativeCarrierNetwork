# imports...
import yaml
from algorithm import AlgorithmBase
import utilities as utils
from cost_model import CostModel
from offer import Offer
import uuid
import numpy as np


class Routing(AlgorithmBase):

    def __init__(self, carrier_id, path_config, path_deliveries):
        self.carrier_id = carrier_id
        self.cost_model = CostModel(path_config)
        self.offers = self.create_offer_list(path_deliveries)
        print(f"\noffer list create, example: {self.offers[0].to_dict()}\n")
        self.depot_location = self.set_depot_location(path_config)
        self.on_auction_indices = []
        locations, assignmets = self.get_locations_and_assignmets()
        print(f"\ncreated locations: {[(round(ll,3),round(lr,3)) for ll, lr in locations]} \nand assignments: {assignmets}\n")

        super().__init__(locations, assignmets)


    def get_mariginal_revenue(self, loc_pickup, loc_dropoff):
        return self.cost_model.get_mariginal_revenue(loc_pickup, loc_dropoff)


    def create_offer_list(self, path_deliveries):
        if not path_deliveries:
            self.deliveries_df = utils.generate_random_locations()
        else:
            self.deliveries_df = utils.read_transport_requests(path_deliveries)
        offers = []
        for i, offer in self.deliveries_df.iterrows():
            offer_id = str(uuid.uuid4())
            loc_pickup = {
                "pos_x": offer.pickup_long, 
                "pos_y": offer.pickup_lat
                }
            loc_dropoff = {
                "pos_x": offer.delivery_long, 
                "pos_y": offer.delivery_lat
                }
            revenue = self.get_mariginal_revenue(loc_pickup, loc_dropoff)
            offers.append(Offer(self.carrier_id, offer_id, loc_pickup, loc_dropoff, revenue=revenue))
        return offers


    def set_depot_location(self, config_file):
        if not config_file:
            loc = (np.random.uniform(0,300), np.random.uniform(0,300)) 
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
    

    def get_requests_below_threshold(self, thresh=100): 
        optimal_tour = self.get_optimal_tour()
        requests_below_thresh = []
        for i, offer in enumerate(self.offers):
            optimal_tour_without_offer = self.get_optimal_tour(ignore_indices=[i])
            margin_distance = float(optimal_tour['distance']) - float(optimal_tour_without_offer['distance'])
            margin_cost = self.cost_model.get_marginal_cost(margin_distance)
            profit = offer.revenue - margin_cost
            if profit < thresh:
                offer.on_auction = True
                offer.profit = profit
                requests_below_thresh.append(offer)
                self.on_auction_indices.append(i)
        self.optimal_tour = self.get_optimal_tour(ignore_indices=self.on_auction_indices)
        return requests_below_thresh


    def calculate_bid(self, loc_pickup, loc_dropoff, revenue):
        optimal_tour = float(self.optimal_tour['distance'])
        optimal_tour_with_offer = float(self.get_optimal_tour(ignore_indices=self.on_auction_indices, include_request=[loc_pickup, loc_dropoff])['distance'])
        margin_distance = optimal_tour_with_offer - optimal_tour
        margin_cost = self.cost_model.get_marginal_cost(margin_distance)
        profit = revenue - margin_cost

        return profit - self.cost_model.threshold


    def update_offer_list(self, offer_to_update):

        if self.carrier_id==offer_to_update['offer_id']:
            for offer in self.offers:
                if offer_to_update['offer_id']==offer.offer_id:
                    offer.winner = offer_to_update['winner']
                    offer.winning_bid = offer_to_update['winning_bid']
        else:
            self.offers.append(self.add_offer(offer_to_update))       


    def add_offer(self, offer):
        carrier_id = offer['offeror']
        offer_id = offer['offer_id']
        loc_pickup = offer['loc_pickup']
        loc_dropoff = offer['loc_dropoff']
        profit = loc_pickup, loc_dropoff
        revenue = offer['revenue']
        return Offer(carrier_id, offer_id, loc_pickup, loc_dropoff, profit, revenue) # offer.on_auction = False by default
        


