from auctioneer import *
import time

if __name__ == "__main__":
    server = Auctioneer(host=socket.gethostname(), port=12345)

    server_thread = threading.Thread(target=server.start)
    server_thread.start()
    
    # wait for x minutes
    time.sleep(60)
    
    # send transport request to first registered client
    if server.connections:
        server.get_TR_from_carrier(server.connections[0][1])

    else: print("No carriers connected to network")