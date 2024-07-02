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

    def __init__(self, carrier_id, path_config=None, n=6):
        # load config file
        config_data = load_config(path_config) if path_config else None
        self.carrier_id = carrier_id
        self.stats = {'revenue':0, 'cost':0, 'profit':0}
        self.cost_model = CostModel(config_data)
        self.depot_location = self.set_depot_location(config_data)
        self.offers = self.create_offer_list(n)
        self.on_auction_indices = []

        locations, assignments = self.get_locations_and_assignments()
        super().__init__(locations, assignments)


    def create_offer_list(self, n):
        path_deliveries = "transport_requests_" + formatted_date + ".csv"
        self.deliveries_df = utils.load_transport_requests(path_deliveries, n)
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
            revenue = self.cost_model.get_mariginal_revenue(loc_pickup, loc_dropoff)
            self.stats['revenue'] += revenue
            offers.append(Offer(self.carrier_id, offer_id, loc_pickup, loc_dropoff, revenue=revenue))
        return offers


    def set_depot_location(self, config_data):
        if not config_data:
            # loc = (np.random.uniform(-100,100), np.random.uniform(-100,100)) 
            # New York City harbor coordinates reach
            loc = (np.random.uniform(81.9698,93.2898), np.random.uniform(37.5281,46.2281)) 
        else:
            loc = config_data['depote_location']
        return loc
    

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
    

    def get_requests_below_threshold(self, thresh=100): 
        if not thresh: 
            thresh = self.cost_model.threshold
        # calcualte optimal tour including all transport requests
        optimal_tour = self.get_optimal_tour()
        requests_below_thresh = []
        for i, offer in enumerate(self.offers):
            # calcualte optimal tour without the i-th transport request
            optimal_tour_without_offer = self.get_optimal_tour(ignore_indices=[i])
            # calcualte marginal distance of the i-th transport request
            margin_distance = float(optimal_tour['distance']) - float(optimal_tour_without_offer['distance'])
            # calcualte marginal cost of the i-th transport request
            margin_cost = self.cost_model.get_marginal_cost(margin_distance)
            # calcualte marginal profit of the i-th transport request
            profit = offer.revenue - margin_cost        
            # update statistics
            self.stats['cost'] += margin_cost
            self.stats['profit'] += profit
            if profit < thresh:
                # set offer on auction
                offer.on_auction = True
                offer.profit = profit
                requests_below_thresh.append(offer)
                # add index of request to list of on auction request indices
                self.on_auction_indices.append(i)
        # update locations and assignments lists such that they do not include requests that are on auction
        if self.on_auction_indices:
            self.delete_location(self.on_auction_indices)
            print(f"\nindices on auction: {self.on_auction_indices}\n")
        # update the optimal tour
        self.optimal_tour = self.get_optimal_tour()
        print(f"\nOptimal tour: {self.optimal_tour}, \nlength: {len(optimal_tour['optimalTour'])}\n")
        # retrun the requests that are for sale
        print(f"statistics: {self.stats}")
        return requests_below_thresh


    def calculate_bid(self, loc_pickup, loc_dropoff, revenue):
        n_jobs = len(loc_pickup) # number of offers in the bundle
        optimal_tour_distance = float(self.optimal_tour['distance'])
        optimal_tour_with_offer_distance = float(self.get_optimal_tour(include_pickups=loc_pickup, include_dropoffs=loc_dropoff)['distance'])
        margin_distance = optimal_tour_with_offer_distance - optimal_tour_distance
        margin_cost = self.cost_model.get_marginal_cost(margin_distance, n_jobs)
        profit = revenue - margin_cost
        return profit - (self.cost_model.threshold*n_jobs)


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
        self.locations = locations; self.assignments = assignments


    def add_offer(self, offer):
        carrier_id = offer['offeror']
        offer_id = offer['offer_id']
        loc_pickup = offer['loc_pickup']
        loc_dropoff = offer['loc_dropoff']
        price = round(float(offer['winning_bid']),2)
        revenue = round(float(offer['revenue']),2)
        self.offers.append(Offer(carrier_id, offer_id, loc_pickup, loc_dropoff, revenue=revenue, winning_bid=price, winner=self.carrier_id)) # offer.on_auction = False by default
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
        assert len(self.locations) == len(offers_not_sold)*2+1
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
            assert len(optimal_tour_without_offer['optimalTour']) == len(self.optimal_tour['optimalTour'])-2
            margin_distance = float(self.optimal_tour['distance']) - float(optimal_tour_without_offer['distance'])
            margin_cost = self.cost_model.get_marginal_cost(margin_distance)
            new_stats['new_cost'] += margin_cost
           
            # add cost of buying offer if offer bought on auction
            if offer.carrier_id != self.carrier_id:
                new_stats['new_cost'] += offer.winning_bid      
            offer.cost = margin_cost 
            if offer.winning_bid!="NONE" and offer.winner!="NONE" and offer.winner != self.carrier_id:
                offer.cost += offer.winning_bid 
            offer.profit = offer.revenue - offer.cost
        new_stats['new_profit']  = new_stats['new_revenue'] - new_stats['new_cost']  
        self.save_print_results(new_stats, save) 


##################
# unused functions
##################

    def get_offers_on_auction(self):
        on_auction_indices = []
        for i, offer in enumerate(self.offers):
            if offer.on_auction:
                on_auction_indices.append(i)
        return on_auction_indices
    

    def update_locations_and_assignments(self, ignore_indices=[], include_pickups=[], include_dropoffs=[]):
        if ignore_indices:
            self.locations, self.assignments = self.filter_requests_by_index(ignore_indices)
        if include_pickups:
            for include_location in zip(include_pickups, include_dropoffs): # zip( [(1,2),()], [(3,4),()] ) -> [ ( (1,2), (3,4) ), () ]
                self.locations.extend(list(include_location)) 
                self.assignments.append([len(self.locations)-2, len(self.locations)-1])