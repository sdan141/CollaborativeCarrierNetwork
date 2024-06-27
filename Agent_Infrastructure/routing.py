# imports...
import yaml
from algorithm import AlgorithmBase
import utilities as utils
from cost_model import CostModel
from offer import Offer
import uuid
import numpy as np
import time


class Routing(AlgorithmBase):

    def __init__(self, carrier_id, path_config, path_deliveries):
        self.stats = {'revenue':0, 'cost':0, 'profit':0}
        self.carrier_id = carrier_id
        self.cost_model = CostModel(path_config)
        self.offers = self.create_offer_list(path_deliveries)
        #print(f"\noffer list create, example: {self.offers[0].to_dict()}\n")
        self.depot_location = self.set_depot_location(path_config)
        self.on_auction_indices = []
        

        t_0 = time.time()
        locations, assignments = self.get_locations_and_assignments()
        #print(f"\nTime to get_locations_and_assignments: {time.time()-t_0}\n")

        #print(f"\ncreated locations: {[(round(ll,3),round(lr,3)) for ll, lr in locations]} \nand assignments: {assignments}\n")

        super().__init__(locations, assignments)
        # print(f"Test: self.locations= {self.locations}\n super.locations= {locations}")


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
            revenue = self.cost_model.get_mariginal_revenue(loc_pickup, loc_dropoff)
            self.stats['revenue'] += revenue
            offers.append(Offer(self.carrier_id, offer_id, loc_pickup, loc_dropoff, revenue=revenue))
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
    

    def get_locations_and_assignments(self): 
        locations = [self.depot_location]
        assignments = []
        for offer in self.offers:
            if offer.winner == "NONE" or offer.winner == self.carrier_id : 
                # interested only in transport requests that were not sold or that were bought by the carrier
                # extract positions and append to locations
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
        '''first the carrier calculate the optimal tour
           then for each offer he calculate the marginal distance (best tour distance - best tour w/o offer distance)
           so he can obtain cost and the marginal profit
           if the profit is below the threshold he sends the offer to the auctioneer
           at the end he calculates again the best tour'''
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
        # update locations and assignments lists such that they do not include requests that are on sale
        if self.on_auction_indices:
            self.delete_location(self.on_auction_indices)
            print(f"\nindices on auction: {self.on_auction_indices}\n")#, \nlocations in tour: {self.locations}\n")
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
                    offer.winning_bid = offer_to_update['winning_bid']
                    if offer.winner == self.carrier_id:
                        offer.on_auction = False
                        # carrier is the winner add location back to tour
                        #self.add_location(add_indices=[i])
                        self.add_location(pickup=[offer_to_update['loc_pickup']], dropoff=[offer_to_update['loc_dropoff']])
                        # if carrier not the winner delete location from tour
                        # self.delete_location(ignore_indices=[i])
                        self.optimal_tour = self.get_optimal_tour()

        else:                  
            # carrier is the winner but not the offeror          
            self.add_offer(offer_to_update)
            self.optimal_tour = self.get_optimal_tour()
            # loc_pickup = []
            # loc_dropoff = []
            # for i in range(len(offer['loc_pickup'])):
            #     loc_pickup.append(tuple(utils.dict_to_float(offer['loc_pickup'][i]).values()))
            #     loc_dropoff.append(tuple(utils.dict_to_float(offer['loc_dropoff'][i]).values()))
            # self.update_locations_and_assignments(include_pickups=loc_pickup, include_dropoffs=loc_dropoff)

            
    
    def update_statistics(self):

        # set unsold offer on_auction=False:
        for offer in self.offers:
            if offer.winner == "NONE":
                offer.on_auction = False

        # get unsold offers
        offers_not_sold = [offer for offer in self.offers if not offer.on_auction and offer.winner=="NONE"]
        # for i in indices_not_sold:
        #     self.offers[i].on_auction = False

        # print(f"\nCheck before update (statistics!!!): self.locations = {[(round(ll,3),round(lr,3)) for ll, lr in self.locations.copy()]}\n, self.assignments = {self.assignments}")
        # print(f"length self.locations: {len(self.locations)}, length self.assignments: {len(self.assignments)}\n")

        # set new locations and assignments lists
        locations, assignments = self.get_locations_and_assignments()
        self.locations, self.assignments = locations, assignments

        # print(f"Check after update (statistics!!!): self.locations = {[(round(ll,3),round(lr,3)) for ll, lr in self.locations.copy()]}\n, self.assignments = {self.assignments}")
        # print(f"length self.locations: {len(self.locations)}, length self.assignments: {len(self.assignments)}\n")
        # loc_pickups = [offer.loc_pickup for i,offer in enumerate(self.offers) if i in indices_not_sold]
        # loc_dropoffs = [offer.loc_dropoff for i,offer in enumerate(self.offers) if i in indices_not_sold]
        # self.add_location(pickup=loc_pickups, dropoff=loc_dropoffs)

        # indices_sold = [i for i in range(len(self.offers)) if self.offers[i].winner!="NONE" and self.offers[i].winner!=self.carrier_id]
        self.optimal_tour = self.get_optimal_tour()
        new_revenue = 0
        new_cost = 0
        new_profit = 0

        # calculate revenue for sold offers
        for offer in self.offers:
            if offer.on_auction:
                new_revenue += offer.winning_bid
                assert offer.winner != "NONE" and offer.winner != self.carrier_id

        # calculate revenue and cost of unsold and bought offers
        for i, offer in enumerate(offers_not_sold):
            optimal_tour_without_offer = self.get_optimal_tour(ignore_indices=[i])
            margin_distance = float(self.optimal_tour['distance']) - float(optimal_tour_without_offer['distance'])
            margin_cost = self.cost_model.get_marginal_cost(margin_distance)
            profit = offer.revenue - margin_cost    

            new_revenue += offer.revenue
            new_cost += margin_cost
            new_profit += profit

            # add cost of buying offer if offer bought on auction
            if offer.carrier_id != self.carrier_id:
                new_cost += offer.winning_bid
                                    
        print(self.stats)
        print(f"\nnew stats: revenue: {new_revenue}, cost: {new_cost}, profit: {new_profit},\nprofit with sold and bought offers: revenue - cost = {new_revenue-new_cost}")


    def add_location(self, pickup=[], dropoff=[]):
        loc_pickup = []
        loc_dropoff = []
        for i in range(len(pickup)):
                loc_pickup.append(tuple(utils.dict_to_float(pickup[i]).values()))
                loc_dropoff.append(tuple(utils.dict_to_float(dropoff[i]).values()))

        # print(f"\nCheck before update: self.locations = {[(round(ll,3),round(lr,3)) for ll, lr in self.locations.copy()]},\n self.assignments = {self.assignments}")
        # print(len(loc_pickup))
        for include_location in zip(loc_pickup, loc_dropoff): # zip( [(1,2),()], [(3,4),()] ) -> [ ( (1,2), (3,4) ), () ]
            self.locations.extend(list(include_location)) 
            self.assignments.append([len(self.locations)-2, len(self.locations)-1])
        # print(f"Check after update: self.locations = {[(round(ll,3),round(lr,3)) for ll, lr in self.locations.copy()]},\n self.assignments = {self.assignments}\n")


    def delete_location(self, ignore_indices):
        # print(f"\nCheck before ignore indices: self.locations = {[(round(ll,3),round(lr,3)) for ll, lr in self.locations.copy()]},\n self.assignments = {self.assignments}")
        # print(f"length self.locations: {len(self.locations)}, length self.assignments: {len(self.assignments)}\n")
        locations = []; assignments = []
        locations, assignments = self.filter_requests_by_index(ignore_indices)
        self.locations = locations; self.assignments =assignments
        # print(f"\nCheck after ignore indices: self.locations = {[(round(ll,3),round(lr,3)) for ll, lr in self.locations.copy()]},\n self.assignments = {self.assignments}")
        # print(f"length self.locations: {len(self.locations)}, length self.assignments: {len(self.assignments)}\n")


    def update_locations_and_assignments(self, ignore_indices=[], include_pickups=[], include_dropoffs=[]):
        if ignore_indices:
            self.locations, self.assignments = self.filter_requests_by_index(ignore_indices)
        if include_pickups:
            for include_location in zip(include_pickups, include_dropoffs): # zip( [(1,2),()], [(3,4),()] ) -> [ ( (1,2), (3,4) ), () ]
                self.locations.extend(list(include_location)) 
                self.assignments.append([len(self.locations)-2, len(self.locations)-1])


    def add_offer(self, offer):
        carrier_id = offer['offeror']
        offer_id = offer['offer_id']
        loc_pickup = offer['loc_pickup']
        loc_dropoff = offer['loc_dropoff']
        price = offer['winning_bid']
        revenue = offer['revenue']
        self.offers.append(Offer(carrier_id, offer_id, loc_pickup, loc_dropoff, revenue=revenue, winning_bid=price, winner=self.carrier_id)) # offer.on_auction = False by default
        self.add_location(pickup=[offer['loc_pickup']], dropoff=[offer['loc_dropoff']])
    


