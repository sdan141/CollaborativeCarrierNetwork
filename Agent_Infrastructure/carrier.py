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
        print("\nTransport requests:\n")
        self.print_offer_list()
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
        
        # offer['loc_pickup'] = [{'pos_x': ..., 'pos_y': ...}, {'pos_x': ..., 'pos_y': ...}]
        else:
            loc_pickup = []
            loc_dropoff = []
            for i in range(len(offer['loc_pickup'])):
                loc_pickup.append(tuple(utils.dict_to_float(offer['loc_pickup'][i]).values()))
                loc_dropoff.append(tuple(utils.dict_to_float(offer['loc_dropoff'][i]).values()))
            
            t_0 = time.time()
            bid = self.routing.calculate_bid(loc_pickup, loc_dropoff, revenue)
            #print(f"\nReal time to calculate bid using manhattan distance: {time.time()-t_0}\n")

        return offer_id, bid
    
    def update_offer_list(self, offer):
        if (offer['offeror']==self.carrier_id and offer['winner']!="NONE") or offer['winner']==self.carrier_id :
            self.routing.update_offer_list(offer)

    def start(self):
        # perform registration
        response = self.request_handler.register()
        if not response or 'payload' not in response or response['payload']['status'] != 'OK':
            print("Registration failed:", response)
            exit()
        
        print(f"\nRegistered for auction!\n")
        # perform sending offers below threshold
        t_0 = time.time()
        requests_below_thresh_list = self.routing.get_requests_below_threshold()
        #print(f"\nTime to get_requests_below_threshold: {time.time()-t_0}\n")
        print(f"\nSending offers with profit below threshold...\n")
        if requests_below_thresh_list:
            for offer in requests_below_thresh_list:
                response = self.request_handler.send_offer(offer) # Send an offer
        else:
            print(f'\n No requests below threshold, you are good to go!\n')
            exit()
            
        auction_time = response["timeout"] #if respond["timeout"]!="NONE" else time.time()+30
        #print(f"\nNext phase: {auction_time}\n")
        self._wait_until(auction_time+1)  # Wait to auction time

        while True:
            # perform request offer
            t_0 = time.time()
            response = self.request_handler.request_offer() # Request current offers
            #print(f"\nTime to recieve answer to request offer: {time.time()-t_0}")
            
            print("\n Auctioneer response to request_offers:")
            if response["payload"]["status"]!="OK":
                print(json.dumps(response, indent=2, default=str))
            else:
                print(json.dumps(response["payload"], indent=2, default=str)) 
            offer = response["payload"]["offer"]
            t_0 = time.time()
            offer_id, bid = self.calculate_bid(offer)
            #print(f"\nTime to calculate bid: {time.time()-t_0}\n")
            
            auction_time = response["timeout"]
            #print(f"\nNext phase: {auction_time}\n")
            self._wait_until(auction_time+1)  # Wait to auction time

            # perform bidding
            t_0 = time.time()
            response = self.request_handler.send_bid(offer_id, bid)  # Send a bid
            #print(f"\nTime to recieve answer to send bid: {time.time()-t_0}")

            print("\n Auctioneer response to bid:")
            if response["payload"]["status"]!="OK":
                print(json.dumps(response, indent=2, default=str))
            else:
                print(json.dumps(response["payload"], indent=2, default=str)) 
            auction_time = response["timeout"]
            #print(f"\nNext phase: {auction_time}\n")
            self._wait_until(auction_time+1)  # Wait to auction time

            # perform request auction results: Receives list of single offers; bundles no longer needed
            response = self.request_handler.request_auction_results()  # Request auction results
            
            print("\n Auctioneer response to request_results:")
            if response["payload"]["status"]!="OK":
                print(json.dumps(response, indent=2, default=str))
            else:
                print(json.dumps(response["payload"], indent=2, default=str)) 

            auction_time = response["timeout"]
            #print(f"\nNext phase: {auction_time}\n")

            self._wait_until(auction_time+1)  # Wait to auction time

            response = self.request_handler.confirm_results()
            print("\n Auctioneer response to confirm_results:")
            print(json.dumps(response["payload"], indent=2, default=str))

            # Response is now list of offers
            # payload: [offer1, offer2, ...]

            received_offers = response["payload"]["offers"]

            t_2 = time.time()
            for received_offer in received_offers:
                self.update_offer_list(received_offer)              
            print(f"\nTime to update offer list: {time.time()-t_2}")

            if not response["payload"]["next_round"]:
                self.print_offer_list()
                #### see which offers were not sold, calculate final profit, compare profits
                self.routing.update_statistics()
                print("\nAuction day over")
                exit()

            auction_time = response["timeout"]
            #print(f"\nNext auction: {auction_time}\n")
            self._wait_until(auction_time+1)
                        

    def print_offer_list(self):
        list_dict = [offer.to_dict() for offer in self.routing.offers]
        utils.print_offer_list(list_dict)