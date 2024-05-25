import socket
import threading
import json
from functools import wraps # takes a function used in a decorator and adds the functionality of copying over the function name, docstring, arguments list, etc.
import time 
import uuid

TIMEOUT = 30

def json_response(action): 
    """
    Decorator to construct and send a JSON response for the auctioneer class
    Parameters:
        action (str): The action type to be included in the response
    Returns:
        decorator (function): The decorator function that wraps the target method
    """
    # *** Make sense or helper func is better (e.g. def create_response(self, carrrier_id, action, req_time, payload) )?
    def func_decorator(func):
        @wraps(func)
        def decorator(*args, **kwargs):
            self, carrier, data = args[:3]  # extracting self, the carrier (socket), and data
            response = {
                "carrier_id": data['carrier_id'],
                "action": action,
                "time": data['time'],
                "timeout": self.auction_time if self.auction_time else "NONE",
                "payload": func(*args, **kwargs)
            }
            #print(f"Sending response: {json.dumps(response, indent=2, default=str)}")

            carrier.send(json.dumps(response).encode('utf-8'))
            carrier.close() 
        return decorator
    return func_decorator


class Offer:
    """
    Class to represent an offer in the auction system
    Attributes:
        carrier_id (str): ID of the carrier who made the offer
        offer_id (str): Unique ID of the offer
        loc_pickup (dict): Pickup coordinates with 'pos_x' and 'pos_y'
        loc_dropoff (dict): Drop-off coordinates with 'pos_x' and 'pos_y'
        bids (dict): Dictionary of bids where keys are carrier IDs and values are bid amounts
    """
    def __init__(self, carrier_id, offer_id, loc_pickup, loc_dropoff, min_price):
        """
        Initialize an Offer object
        """
        self.carrier_id = carrier_id    # id of offeror carrier
        self.offer_id = offer_id        # uniq offer id
        self.loc_pickup = loc_pickup
        self.loc_dropoff = loc_dropoff
        self.min_price = min_price
        self.bids = {}                  # dictionary for bids key: biding carrir id, value: numeric bid value 

    def add_bid(self, bidder ,bid):
        """
        Add a bid to the offer
        Parameters:
            bidder (str): ID of the carrier making the bid
            bid (float): The bid amount
        """
        self.bids[bidder] = bid

    def get_highest_bid(self):
        """
        Get the highest bid for the offer
        Returns:
            tuple: A tuple containing the highest bid carrier ID and the bid amount, or None if no bids exist
        """
        if not self.bids:
            return False 
        else:
            highest_bid = max(self.bids.items(), key=lambda k: k[1])
            return highest_bid
    
    def to_dict(self):
        """
        Convert the Offer object to a dictionary
        Returns: The dictionary representation of the offer
        """
        return {
            "offeror": self.carrier_id,
            "offer_id": self.offer_id,
            "loc_pickup": self.loc_pickup,
            "loc_dropoff": self.loc_dropoff,
            "min_price": self.min_price
            #"bids": self.bids
        }


class Auctioneer:
    """
    Class to represent the auctioneer in the transport auction system
    Attributes:
        auctioneer_socket (socket.socket): The server socket to listen for connections
        registered_carriers (list): List of registered carriers IDs
        offers (dict): Key is ID of offer, value is the offer object
        auction_time (float): Timestamp for the next auction
        fetched_results (list): List of registered carriers IDs which already fetched the results
    """
    def __init__(self, host=socket.gethostname(), port=12349):
        """
        Initialize the Auctioneer object
        Parameters:
            host (str): Host address for the server. Default is 'localhost'
            port (int): Port number for the server. Default is 12345
        """
        self.host = host
        self.port = port
        self.registered_carriers = [] 
        self.offers = {}
        self.auction_time = None
        self.fetched_results = [] 
        self.phase = "REGIST" # new code
        self.next_round = True
        self._stop_event = threading.Event()

    def start_server(self):
        """
        Start the auctioneer server to listen for incoming connections
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print("Auctioneer server started, waiting for connections...")

        auction_thread = threading.Thread(target=self.handle_auction_phases)
        auction_thread.start()

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr} has been established.")
            carrier_handler = threading.Thread(target=self.handle_carrier, args=(client_socket,))
            carrier_handler.start()

    def handle_auction_phases(self):
        while not self._stop_event.is_set():
            if self.auction_time is not None:
                for i in range(5):
                    if not i:
                        self._wait_until(self.auction_time)
                    self.phase = "REQ_OFFER"
                    print("\nEntering offer request phase")
                    self.auction_time = int(time.time()) + TIMEOUT
                    self._wait_until(self.auction_time)

                    self.phase = "BID"
                    print("\nEntering bidding phase")
                    self.auction_time = int(time.time()) + TIMEOUT
                    self._wait_until(self.auction_time)

                    self.phase = "RESULT"
                    print("\nEntering results phase")
                    if self.offers:
                        if not any([offer.get_highest_bid() for offer in self.offers.values()]):
                            self.next_round = False

                    self.auction_time = int(time.time()) + TIMEOUT
                    self._wait_until(self.auction_time)
                    if not self.next_round:
                        print("\nAuction day closed server restarts tomorrow...")
                        self.stop_server()
                        break
                    else:
                        for offer_id in list(self.offers):
                            if self.offers[offer_id].bids:
                                del self.offers[offer_id]


    def _wait_until(self, timeout):
        while time.time() < timeout:
            if self._stop_event.is_set():
                return
            time.sleep(1)

    def stop_server(self):
        self._stop_event.set()
        if self.server_socket:
            self.server_socket.close()     
        exit()    

    def handle_carrier(self, carrier_socket):
        """
        Handle incoming requests from carriers
        Parameters:
            carrier_socket (socket.socket): The client (carrier) socket connection
        """
        try:
            message = carrier_socket.recv(1024).decode('utf-8')
            if message:
                data = json.loads(message)
                action = data['action']

                if action == 'register':
                    self.register_carrier(carrier_socket, data)
                elif action == 'offer':
                    if self.auction_time is None and data['carrier_id'] in self.registered_carriers:
                        self.auction_time = int(time.time()) + TIMEOUT
                    self.receive_offer(carrier_socket, data)
                elif action == 'request_offers':
                    self.send_offers_list(carrier_socket, data)
                elif action == 'bid':
                    self.receive_bid(carrier_socket, data)
                elif action == 'request_auction_results':
                    self.send_results(carrier_socket, data)
                # else: self.invalid_action(carrier_socket, data)

        except Exception as e:
            print(f"\nError occure during handling connection with carrier {carrier_socket.getpeername()}. \nError : {e}\n")
        carrier_socket.close()
        

    @json_response("register")
    def register_carrier(self, carrier, data):
        """
        Register a carrier
        Parameters:
            carrier (socket.socket): The client (carrier) socket connection
            data (dict): The JSON data received from the client
        Returns:
            dict: The payload for the response
        """
        carrier_id = data['carrier_id']
        if self.phase != "REGIST":
            return {"status": "NO_REGISTRATION_PHASE"}
        if carrier_id in self.registered_carriers:
            return {"status": "ALREADY_REGISTERED"}
        self.registered_carriers.append(carrier_id)
        return {"status": "OK"}


    @json_response("offer")
    def receive_offer(self, carrier, data):
        """
        Receive an offer from a carrier
        """
        carrier_id = data['carrier_id']
        if self.phase != "REGIST": 
            return {"response": "OFFER_SUBMISSION_TIMEOUT"}
        if carrier_id not in self.registered_carriers:
            return {"response": "NOT_REGISTERED"}
    
        offer_id = data['payload']['offer_id']
        loc_pickup = data['payload']['loc_pickup']
        loc_dropoff = data['payload']['loc_dropoff']
        min_price = data['payload']['profit']
        offer = Offer(carrier_id, offer_id, loc_pickup, loc_dropoff, min_price)
        self.offers[offer_id] = offer
        #if self.auction_time is None:
        #    self.auction_time = int(time.time()) + TIMEOUT

        payload = {
            "offer_id": offer_id,
            "response": "OK"
            #"next_auction": self.auction_time
        }
        return payload
        
    @json_response("request_offers")
    def send_offers_list(self, carrier, data):
        """
        Send the list of current offers to a carrier
        """
        carrier_id = data['carrier_id']
        if self.phase != "REQ_OFFER": 
            return {"status": "OFFER_REQUEST_TIMEOUT"}
        if carrier_id not in self.registered_carriers:
            return {"status": "NOT_REGISTERED"}
        if  not self.offers:
            return {"status": "NO_OFFERS_AVAILABLE"}
        offer_list = [offer.to_dict() for offer in self.offers.values()]
        payload = {
            "status": "OK",
            #"next_auction": self.auction_time
            "offer_list": offer_list
        }
        return payload

    @json_response("bid")
    def receive_bid(self, carrier, data):
        """
        Receive a bid from a carrier
        """
        carrier_id = data['carrier_id']
        if self.phase != "BID":
            return {"status": "BIDDING_TIMEOUT"}
        if carrier_id not in self.registered_carriers:
            return {"status": "NOT_REGISTERED"}
        offer_id = data['payload']['offer_id']
        bid = data['payload']['bid']
        if offer_id in self.offers:
            if bid > self.offers[offer_id].min_price:
                self.offers[offer_id].add_bid(carrier_id, bid)
                payload = {
                    "status": "OK",
                    "offer_id": offer_id
                    #"results_time": self.auction_time
                }
        else:
            payload = {"status": "INVALID_OFFER_ID"}
        return payload

    @json_response("request_auction_results")
    def send_results(self, carrier, data):
        """
        Send the auction results to a carrier.
        """
        carrier_id = data['carrier_id']
        if carrier_id not in self.registered_carriers:
            return {"status": "NOT_REGISTERED"}
        if self.phase != "RESULT":
            return {"status": "NO_RESULTS_PHASE"}
        self.fetched_results.append(carrier_id)
        result_list = []
        for offer_id, offer in self.offers.items():
            highest_bid = offer.get_highest_bid()
            if highest_bid:
                winner_carrier_id, winning_bid = highest_bid
            else:
                winner_carrier_id, winning_bid = ("NONE", "NONE")

            result_list.append({
                "offer_id": offer_id,
                "winner_carrier_id": winner_carrier_id,
                "winning_bet": winning_bid,
                "loc_pickup": offer.loc_pickup,
                "loc_dropoff": offer.loc_dropoff
            })
        payload = {
                "status": "OK",
                "offer_list": result_list,
                #"next_auction": self.auction_time,
                "next_round": str(self.next_round)
        }
        return payload
