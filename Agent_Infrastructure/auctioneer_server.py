import socket
import threading
from auctioneer import Auctioneer
from carrier_handler import CarrierHandler

class AuctioneerServer:
    """
    Class to represent the auctioneer server handling all communication.
    """
    def __init__(self, host=socket.gethostname(), port=12349):
        self.host = host
        self.port = port
        self.auctioneer = Auctioneer()
        self._stop_event = threading.Event()

    def start_server(self):
        auction_thread = threading.Thread(target=self.auctioneer.handle_auction_phases)
        auction_thread.start()

        connection_thread = threading.Thread(target=self.handle_connections)
        connection_thread.start()

        auction_thread.join()
        self.stop_server()

    def handle_connections(self):
        with threading.Lock():   
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print("Auctioneer server started, waiting for connections...")

        while not self._stop_event.is_set():
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr} has been established.")
            carrier_handler = CarrierHandler(self.auctioneer, client_socket)
            carrier_handler.start()

    def stop_server(self):
        self._stop_event.set()
        if self.server_socket:
            self.server_socket.close()
        exit()