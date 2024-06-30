import socket
import threading
import json
import time
import re
import utilities as utils
import traceback #tmp


BASE_TIMEOUT = 10

class CarrierHandler(threading.Thread):

    def __init__(self, auctioneer, carrier_socket):
        super().__init__()
        self.auctioneer = auctioneer
        self.carrier_socket = carrier_socket

    def run(self):
        try:
            message = self.carrier_socket.recv(1024).decode('utf-8')
            if message:
                data = json.loads(message)
                action = data['action']
                if action == 'register':
                    self.register_carrier(data)
                elif action == 'offer':
                    if self.auctioneer.auction_time is None and data['carrier_id'] in self.auctioneer.registered_carriers:
                        self.auctioneer.auction_time = int(time.time()) + 2*BASE_TIMEOUT
                    self.receive_offer(data)
                elif action == 'request_offer':
                        self.send_offer(data)
                elif action == 'bid':
                    self.receive_bid(data)
                elif action == 'request_auction_results':
                    self.send_results(data)
                elif action == 'confirm':
                    self.confirm(data)
                else:
                    self.carrier_socket.close()
                    print("Invalid action from carrier. Connection closed.")
        except Exception as e:
            print(f"\nError occurred during handling connection with carrier. \nError: {e}\n")
            print(traceback.format_exc()) #tmp
        self.carrier_socket.close()


    def send_response(action):
        """
        Decorator to construct and send a JSON response to the carrier.
        """
        def func_decorator(func):
            def decorator(self, data):
                response = {
                    "carrier_id": data['carrier_id'],
                    "action": action,
                    "time": data['time'],
                    "timeout": self.auctioneer.auction_time if self.auctioneer.auction_time else "NONE",
                    "payload": func(self, data)
                }
                self.carrier_socket.send(json.dumps(response).encode('utf-8'))
                self.carrier_socket.close()
            return decorator
        return func_decorator


    @send_response("register")
    def register_carrier(self, data):
        """
        Register a carrier.
        """
        carrier_id = data['carrier_id']
        if self.auctioneer.phase != "REGIST":
            return {"status": "NO_REGISTRATION_PHASE"}
        if carrier_id in self.auctioneer.registered_carriers:
            return {"status": "ALREADY_REGISTERED"}
        self.auctioneer.registered_carriers.append(carrier_id)
        return {"status": "OK"}


    @send_response("offer")
    def receive_offer(self, data):
        """
        Receive an offer from a carrier.
        """
        carrier_id = data['carrier_id']
        if self.auctioneer.phase != "REGIST":
            return {"response": "OFFER_SUBMISSION_TIMEOUT"}
        if carrier_id not in self.auctioneer.registered_carriers:
            return {"response": "NOT_REGISTERED"}
        self.auctioneer.add_offer(carrier_id, data['payload'])
        payload = {
            "offer_id": data['payload']['offer_id'],
            "response": "OK"
        }
        return payload


    @send_response("request_offer")
    def send_offer(self, data):
        """
        Send the current offer on auction.
        """
        carrier_id = data['carrier_id']
        if self.auctioneer.phase != "REQ_OFFER":
            return {"status": "OFFER_REQUEST_TIMEOUT"}
        elif carrier_id not in self.auctioneer.registered_carriers:
            return {"status": "NOT_REGISTERED"}
        elif not self.auctioneer.offers:
            return {"status": "NO_OFFERS_AVAILABLE"}
        loc_pickup = []
        loc_dropoff = []
        revenue = 0 
        '''
        for offer in self.auctioneer.offers:
        '''
        for i in self.auctioneer.indices_on_auction:
            offer = self.auctioneer.offers[i]
            if offer.on_auction:
                loc_pickup.append(offer.loc_pickup) #{'pos_x':.., 'pos_y': ...}
                loc_dropoff.append(offer.loc_dropoff)
                revenue += offer.revenue
        payload = {
            "status": "OK",
            "offer": {
                "offer_id": self.auctioneer.id_on_auction, # boundle id for bundle
                "loc_pickup": loc_pickup,
                "loc_dropoff": loc_dropoff,
                "revenue": revenue
                }}
        if not loc_pickup:
            return {"status": "NO_ACTIVE_OFFERS"} 
        return payload
        

    @send_response("bid")
    def receive_bid(self, data):
        """
        Receive a bid from a carrier.
        """
        error = 1

        carrier_id = data['carrier_id']
        if self.auctioneer.phase != "BID":
            print("Bidding timeout, current phase: ", self.auctioneer.phase)
            return {"status": "BIDDING_TIMEOUT"}
        if carrier_id not in self.auctioneer.registered_carriers:
            return {"status": "NOT_REGISTERED"}
        
        offer_id = data['payload']['offer_id']
        bid = data['payload']['bid']
        #for offer in self.auctioneer.offers:
        for i in self.auctioneer.indices_on_auction:
            offer = self.auctioneer.offers[i]
            #check if it is bundle
            if re.match("bundle_.*", offer_id): # Case: Bundle
                # Get bundle_key to access the offers in bundles
                first_offer_in_bundle = offer_id.replace("bundle_", "")
                bundle_key = utils.get_key_from_bundle_by_first_element(self.auctioneer.bundles, first_offer_in_bundle)
                # Check if offer is in Bundle
                if offer.offer_id in self.auctioneer.bundles[bundle_key]:
                    # obtain bid and distribute it to all single offers; here one case
                    bid_share = self.auctioneer.calculate_share(offer.offer_id, bid)
                    offer.add_bid(carrier_id, bid_share)
                    error = 0
            else: # Case: No Bundle (Single Offer)
                if offer.offer_id == offer_id and offer.on_auction:
                    offer.add_bid(carrier_id, bid)
                    error = 0
        # Send response here
        if not error:
            payload = {
                "status": "OK",
                "offer_id": offer_id
                }
            return payload
        return {"status": "INVALID_BID"}
        

    @send_response("request_auction_results")
    def send_results(self, data):
        """
        Send the auction results to a carrier.
        """
        carrier_id = data['carrier_id']
        if carrier_id not in self.auctioneer.registered_carriers:
            return {"status": "NOT_REGISTERED"}
        if self.auctioneer.phase != "RESULTS":
            return {"status": "NO_RESULTS_PHASE"}
        
        self.auctioneer.active_carriers.append(carrier_id)
        results_available = 0
        offers_on_auction = []

        for i in self.auctioneer.indices_on_auction:
                offers_on_auction.append(self.auctioneer.offers[i])
                results_available = True

        if results_available:
            # send results
            payload = {
                "status": "OK",
                "offers": [ob.to_dict() for ob in offers_on_auction]
            }
            return payload
        return {"status": "NO_RESULTS_AVAILABLE"}

    @send_response("confirm")
    def confirm(self, data):
        """
        Confirm results and next round.
        """
        carrier_id = data['carrier_id']
        if self.auctioneer.phase != "CONFIRM":
            return {"status": "CONFIRMATION_TIMEOUT"}
        if carrier_id not in self.auctioneer.registered_carriers:
            return {"status": "NOT_REGISTERED"}
        
        results_available = 0
        offers_on_auction = []
        for i in self.auctioneer.indices_on_auction:
                offers_on_auction.append(self.auctioneer.offers[i])
                results_available = 1

        if results_available:
            # send results
            payload = {
                "status": "OK",
                "offers": [ob.to_dict() for ob in offers_on_auction],
                "next_round": self.auctioneer.next_round
            }
            return payload
        
        return {"status": "NO_CONFIRMATION_AVAILABLE"}