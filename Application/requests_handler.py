import socket
import json
import time
import uuid

class RequestHandler:

    def __init__(self, carrier_id, server_host, server_port):
        self.carrier_id = carrier_id
        self.server_host = server_host
        self.server_port = server_port

    def connect_to_auctioneer(self):
        carrier_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            carrier_socket.connect((self.server_host, self.server_port))
        except ConnectionRefusedError as e:
            self.socketio.emit(self.carrier_id, {'message': f"Error connecting to Auctioneer server: {e}", "action": "log"})
            print(f"Error connecting to Auctioneer server: {e}")
            return None
        return carrier_socket

    def send_request(self, action, payload):
        with self.connect_to_auctioneer() as carrier_socket:
            if carrier_socket is None:
                return {"error": "Connection error"}
            request = {
                "carrier_id": self.carrier_id,
                "action": action,
                "time": str(int(time.time())),
                "payload": payload
            }
            carrier_socket.send(json.dumps(request).encode('utf-8'))
            response = carrier_socket.recv(1024)
            try:
                return json.loads(response.decode('utf-8'))
            except json.JSONDecodeError:
                return {"error": "Failed to decode JSON response"}

    def register(self):
        return self.send_request("register", {})

    def send_offer(self, offer):
        payload = {
            "offer_id": offer.offer_id,
            "loc_pickup": offer.loc_pickup,
            "loc_dropoff": offer.loc_dropoff,
            "profit": offer.profit,
            "revenue": offer.revenue
        }
        return self.send_request("offer", payload)

    def request_offer(self):
        return self.send_request("request_offer", {})

    def send_bid(self, offer_id, bid):
        payload = {
            "offer_id": offer_id,
            "bid": bid
        }
        return self.send_request("bid", payload)

    def request_auction_results(self):
        return self.send_request("request_auction_results", {})
    
    def confirm_results(self):
        return self.send_request("confirm", {})



# self.socketio.emit(self.carrier_id, {'message': f"Error connecting to Auctioneer server: {e}"})