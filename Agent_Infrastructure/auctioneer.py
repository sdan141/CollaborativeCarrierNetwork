import time
from carrier_handler import CarrierHandler
from offer import Offer

BASE_TIMEOUT = 5
MAX_ROUNDS = 5

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
    def __init__(self):

        self.offers = []
        self.registered_carriers = [] 
        self.active_carriers = []
        self.auction_time = None
        self.next_round = True
        

    def handle_auction_phases(self):
        while self.next_round:
            if self.auction_time is not None: # at least one registered carrier has sent offers
                for n_round in range(MAX_ROUNDS): # iterating rounds
                    sold = 0 # for counting how many offers have been sold in the round

                    for i in range(len(self.offers)): # iterating auction list
                        if not n_round:
                            self._wait_until(self.auction_time)

                        self.phase = "REQ_OFFER"
                        auction = self.offers[i]
                        auction.on_auction = True
                        print("\nEntering offer request phase")
                        self.auction_time = int(time.time()) + BASE_TIMEOUT
                        self._wait_until(self.auction_time)

                        self.phase = "BID"
                        print("\nEntering bidding phase")
                        self.auction_time = int(time.time()) + BASE_TIMEOUT
                        self._wait_until(self.auction_time)

                        self.phase = "RESULT"
                        auction.update_results()
                        print("\nEntering results phase")
                        self.auction_time = int(time.time()) + BASE_TIMEOUT
                        self._wait_until(self.auction_time)

                        self.phase = "CONFIRM"
                        self.check_active_carriers()
                        if auction.winner != "NONE":
                            sold += 1

                        if len(self.offers)-1 == i:
                            if not sold and not auction.bids: # no offer was sold and the current offer has no valid bids
                                self.next_round = False
                            self.update_auction_list()
                        self._wait_until(self.auction_time)
                        auction.on_auction = False

                    if not self.next_round:
                        print("\nAuction day closed server restarts tomorrow...")
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