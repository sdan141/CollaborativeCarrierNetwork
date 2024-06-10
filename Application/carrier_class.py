import socket
import json
from functools import wraps
import time
import uuid

from flask_socketio import SocketIO, emit
import socket

def json_request(func):
    """
    Decorator to handle the sending of requests and receiving of responses for the Carrier class
    Establishes and closes the connection for each request to prevent server overload
    Parameters:
        func (function): The function to be decorated
    Returns:
        wrapper: The decorated function
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        carrier_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            carrier_socket.connect((self.server_host, self.server_port))
        except ConnectionRefusedError as e:
            print(f"Error connection to Auctioneer server. Server is down or unavailable of this port. Error: {e}")
            self.socketio.emit(self.carrier_id, {'message': f"Error connection to Auctioneer server. Server is down or unavailable of this port. Error: {e}"})

        action, payload = func(self, *args, **kwargs)
        request = {
            "carrier_id" : self.carrier_id,
            "action"     : action,
            "time"       : str(int(time.time())),
            "payload"    : payload
        }
        carrier_socket.send(json.dumps(request).encode('utf-8'))
        response = b""
        while True:
            part = carrier_socket.recv(1024)
            if not part:
                break
            response += part
        #response = carrier_socket.recv(1024).decode('utf-8')
        
        carrier_socket.close()

        try:
            return json.loads(response.decode('utf-8'))
        except json.JSONDecodeError:
            print("Failed to decode JSON response:", response)
            return json.loads(response)
    return wrapper


class Carrier:
    """
    Class to represent a carrier in the transport auction system
    Attributes:
        carrier_id (str): Unique ID of the carrier
        server_host (str): Host address of the auctioneer server
        server_port (int): Port number of the auctioneer server
    """
    def __init__(self, carrier_id, socketio, server_host=socket.gethostname(), server_port=12349):
        """
        Initialize the Carrier object
        """
        self.carrier_id = carrier_id
        self.server_host = server_host
        self.server_port = server_port
        self.socketio = socketio
        print(f"Carrier agent {carrier_id} is ready")
        self.socketio.emit(carrier_id, {'message': f"Carrier agent {carrier_id} is ready"})

    @json_request
    def register(self):
        """
        Register the carrier with the auctioneer server
        """
        self.socketio.emit(self.carrier_id, {'message': "Registering for auction..."})
        return "register", {}

    @json_request
    def send_offer(self, loc_pickup, loc_dropoff, profit):
        """
        Send an offer to the auctioneer server.
        Parameters:
            loc_pickup (dict): Pickup coordinates with 'pos_x' and 'pos_y'
            loc_dropoff (dict): Drop-off coordinates with 'pos_x' and 'pos_y'
        """
        offer_id = str(uuid.uuid4())
        payload = {
            "offer_id"    : offer_id,
            "loc_pickup"  : loc_pickup,
            "loc_dropoff" : loc_dropoff,
            "profit"      : profit
        }
        return "offer", payload

    @json_request
    def request_offers(self):
        """
        Request the list of current offers from the auctioneer server
        """
        return "request_offers", {}

    @json_request
    def send_bid(self, offer_id, bid):
        """
        Send a bid to the auctioneer server
        Parameters:
            offer_id (str): Unique ID of the offer
            bid (float): The bid amount
        """
        payload = {
            "offer_id": offer_id,
            "bid": bid
        }
        return "bid", payload

    @json_request
    def request_auction_results(self):
        """
        Request the auction results from the auctioneer server
        """
        return "request_auction_results", {}
    


