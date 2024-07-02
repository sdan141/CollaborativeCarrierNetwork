import numpy as np
import yaml
import uuid
import utilities as utils
from algorithm import AlgorithmBase
from cost_model import CostModel
from offer import Offer
from datetime import datetime

current_date = datetime.now()
formatted_date = current_date.strftime('%y%m%d')

def load_config(config_file):
    """
    Load configuration data from a YAML file
    Args:
        config_file (str): Path to the configuration file
    Returns:
        dict: Configuration data
    """
    with open(config_file, 'rb') as stream:
        try:
            config_data = yaml.safe_load(stream)
            return config_data
        except yaml.YAMLError as e:
            print(e)
            return None


class Routing(AlgorithmBase):

    def __init__(self, carrier_id, socketio, dt_data, depot, cost_model):
        self.carrier_id = carrier_id
        self.socketio = socketio
        self.deliveries_df = dt_data
        self.depot_location = depot 
        self.cost_model = CostModel(cost_model)
        self.stats = {'revenue':0, 'cost':0, 'profit':0}
        self.offers = self.create_offer_list()
        self.on_auction_indices = []
        
        locations, assignments = self.get_locations_and_assignments()
        super().__init__(locations, assignments)

        
    def create_offer_list(self):
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
            revenue = offer.revenue 
            min_price = offer.profit
            cost = offer.cost
            self.stats['revenue'] += revenue
            self.stats['profit'] += min_price
            self.stats['cost'] += cost
            offers.append(Offer(self.carrier_id, offer_id, loc_pickup, loc_dropoff, revenue, min_price))
        return offers

    def get_locations_and_assignments(self): 
        locations = [self.depot_location]
        assignments = []
        for offer in self.offers:
            if offer.on_auction == False : 
                # interested only in transport requests that were not sold or that were bought by the carrier
                # extract positions and append to locations
                pickup_index = len(locations)  # Index of the next pickup location
                locations.append((offer.loc_pickup["pos_x"], offer.loc_pickup["pos_y"]))
                dropoff_index = len(locations)  # Index of the next dropoff location
                locations.append((offer.loc_dropoff["pos_x"], offer.loc_dropoff["pos_y"]))
                # Append the indices to the assignment list
                assignments.append([pickup_index, dropoff_index])
        return locations, assignments
    
    def get_requests_below_threshold(self): 
        requests_below_thresh = []
        for i, offer in enumerate(self.offers):
            if offer.min_price < self.cost_model.sell_threshhold:
                offer.on_auction = True
                requests_below_thresh.append(offer)
                self.on_auction_indices.append(i)
        # update locations and assignments lists such that they do not include requests that are on auction
        if self.on_auction_indices:
            self.delete_location(self.on_auction_indices)
            print(f"Indices on auction: {self.on_auction_indices}\n")
        return requests_below_thresh


    def calculate_bid(self, loc_pickup, loc_dropoff, revenue):
        optimal_tour_distance = float(self.get_optimal_tour(ignore_indices=self.on_auction_indices)['distance'])
        optimal_tour_with_offer_distance = float(self.get_optimal_tour(ignore_indices=self.on_auction_indices,\
                                                              include_pickups=loc_pickup, include_dropoffs=loc_dropoff)['distance'])
        added_distance = optimal_tour_with_offer_distance - optimal_tour_distance
        added_cost = self.cost_model.b1 + self.cost_model.b2 * (added_distance / 1000)
        bid = revenue - added_cost - self.cost_model.buy_threshold
        return bid


    def update_offer_list(self, offer_to_update):
        if self.carrier_id==offer_to_update['offeror']:
            # carrier is the offeror and maybe the winner
            for i,offer in enumerate(self.offers):
                if offer_to_update['offer_id']==offer.offer_id:
                    offer.winner = offer_to_update['winner']
                    offer.winning_bid = round(float(offer_to_update['winning_bid']),2)
                    if offer.winner == self.carrier_id:
                        offer.on_auction = False
                        # carrier is the winner -> add location back to tour
                        self.add_location(pickup=[offer_to_update['loc_pickup']], dropoff=[offer_to_update['loc_dropoff']])
                        self.optimal_tour = self.get_optimal_tour()
        else:                  
            # carrier is the winner but not the offeror          
            self.add_offer(offer_to_update)
            self.optimal_tour = self.get_optimal_tour()
        # if carrier was the seller no need to calculate optimal tour...


    def add_location(self, pickup=[], dropoff=[]):
        loc_pickup = []
        loc_dropoff = []
        for i in range(len(pickup)):
                loc_pickup.append(tuple(utils.dict_to_float(pickup[i]).values()))
                loc_dropoff.append(tuple(utils.dict_to_float(dropoff[i]).values()))

        for include_location in zip(loc_pickup, loc_dropoff): # zip( [(1,2),()], [(3,4),()] ) -> [ ( (1,2), (3,4) ), () ]
            self.locations.extend(list(include_location)) 
            self.assignments.append([len(self.locations)-2, len(self.locations)-1])


    def delete_location(self, ignore_indices):
        locations = []; assignments = []
        locations, assignments = self.filter_requests_by_index(ignore_indices)
        self.locations = locations; self.assignments =assignments


    def add_offer(self, offer):
        carrier_id = offer['offeror']
        offer_id = offer['offer_id']
        loc_pickup = offer['loc_pickup']
        loc_dropoff = offer['loc_dropoff']
        price = round(float(offer['winning_bid']),2)
        revenue = round(float(offer['revenue']),2)
        min_price = round(float(offer['min_price']),2)
        self.offers.append(Offer(carrier_id, offer_id, loc_pickup, loc_dropoff, revenue, min_price, winning_bid=price, winner=self.carrier_id)) # offer.on_auction = False by default
        self.add_location(pickup=[offer['loc_pickup']], dropoff=[offer['loc_dropoff']])


    def save_print_results(self, new_stats, save):
        difference = new_stats['new_profit'] - self.stats['profit']
        increase = (difference / abs(self.stats['profit'])) * 100 if self.stats['profit'] != 0 else np.int
        new_stats = {k: round(v, 2) for k, v in new_stats.items()}
        old_stats = {k: round(v, 2) for k, v in self.stats.items()}
        difference = round(difference, 2)
        increase = round(increase, 2)
        if save:
            utils.save_results_to_csv(formatted_date, old_stats['profit'], new_stats['new_profit'], difference, increase)
        print(f"\nBefore aution day: {old_stats}\nAfter auction day: {new_stats}\nIncrease: {increase}%\n") 
    

    def update_statistics(self, save=True):
        # set unsold offer on_auction=False:
        for offer in self.offers:
            if offer.winner == "NONE":
                offer.on_auction = False
        # get ALL unsold offers
        offers_not_sold = [offer for offer in self.offers if not offer.on_auction]
        # set new locations and assignments lists
        locations, assignments = self.get_locations_and_assignments()
        self.locations, self.assignments = locations, assignments
        self.optimal_tour = self.get_optimal_tour()
        new_stats = {
        'new_revenue': 0,
        'new_cost': 0,
        'new_profit': 0
        }
        # calculate revenue for sold offers
        for offer in self.offers:
            if offer.on_auction:
                new_stats['new_revenue'] += offer.winning_bid
                assert offer.winner != "NONE" and offer.winner != self.carrier_id
        # calculate revenue and cost of unsold and bought offers
        for i, offer in enumerate(offers_not_sold):
            new_stats['new_revenue'] += offer.revenue
            
            optimal_tour_without_offer = self.get_optimal_tour(ignore_indices=[i])
            margin_distance = float(self.optimal_tour['distance']) - float(optimal_tour_without_offer['distance'])
            margin_cost = self.cost_model.get_marginal_cost(margin_distance)
            new_stats['new_cost'] += margin_cost
           
            # add cost of buying offer if offer bought on auction
            if offer.carrier_id != self.carrier_id:
                new_stats['new_cost'] += offer.winning_bid      
            offer.cost = margin_cost + (offer.winning_bid if offer.winning_bid!="NONE" else 0) 
            offer.profit = offer.revenue - offer.cost
        new_stats['new_profit']  = new_stats['new_revenue'] - new_stats['new_cost']  
        self.save_print_results(new_stats, save) 



    



"""
def get_requests_below_threshold(self):
        requests_below_thresh = []
        print()
        for i, offer in enumerate(self.offers):
            if offer.profit < float(self.cost_model.sell_threshhold):
                self.socketio.emit(self.carrier_id, {'message': f"Sending offer with profit: {offer.profit}€!", "action": "log"})
                offer.on_auction = True
                requests_below_thresh.append(offer)
                self.on_auction_indices.append(i)
        return requests_below_thresh


    def calculate_bid(self, loc_pickup, loc_dropoff, revenue, min_price):
        optimal_tour_distance = float(self.get_optimal_tour(ignore_indices=self.on_auction_indices)['distance'])
        optimal_tour_with_offer_distance = float(self.get_optimal_tour(ignore_indices=self.on_auction_indices,\
                                                   include_pickups=loc_pickup, include_dropoffs=loc_dropoff)['distance'])
        margin_distance = optimal_tour_with_offer_distance - optimal_tour_distance
        margin_cost = self.cost_model.get_marginal_cost(margin_distance)
        bid = round(revenue - margin_cost - float(self.cost_model.buy_threshhold), 2)
        print(f"Revenue: {revenue}")
        print(f"Margin cost: {margin_cost}")
        print(f"Calculated bid: {bid}")
        if bid < min_price:
            bid  = 0
        return bid
"""