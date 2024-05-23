from carrier_class import *
import sys
import utilities as utils

def start_carrier(carrierId, locations, deliveries, revenues, socketio):
    carrier = Carrier(carrierId, socketio)
    respond = carrier.register() # Register the carrier
    print("\n Auctioneer response to register:")
    print(json.dumps(respond, indent=2, default=str))
    message =  "Auctioneer response: " + json.dumps(respond, indent=2, default=str)
    socketio.emit(carrierId, {'message': message })
    
    if respond['payload']['status'] == 'OK':

        ### Decide which offers to send (i.e. calculate offers below threshold)

        # Example offer
        pickup = {"pos_x": "10", "pos_y": "-10"}
        dropoff = {"pos_x": "0", "pos_y": "0"}

        file_path = f"example_TR_{carrier.carrier_id}.csv"

        deliveries_df = utils.read_transport_requests(file_path, carrierId, socketio)

        requests_below_thresh_list = utils.get_requests_below_thresh(deliveries_df, carrierId, socketio)
        if requests_below_thresh_list:
            for loc_pickup, loc_dropoff, profit in requests_below_thresh_list:
                respond = carrier.send_offer(loc_pickup, loc_dropoff, profit) # Send an offer
                print("\n Auctioneer response to offer:")
                print(json.dumps(respond, indent=2, default=str))
                message =  "Auctioneer response to offer: " + json.dumps(respond, indent=2, default=str)
                socketio.emit(carrierId, {'message': message })

                ### Update transport network
                    

            auction_time = respond["timeout"] # If respond["timeout"]!="NONE" else time.time()+30
            time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time

            while True:
                respond = carrier.request_offers() # Request current offers
                print("\n Auctioneer response to request_offers:")
                print(json.dumps(respond, indent=2, default=str))
                message =  "Auctioneer response to request_offers: " + json.dumps(respond, indent=2, default=str)
                socketio.emit(carrierId, {'message': message })

                offers = respond["payload"]["offer_list"]

                ## Calculate bids for each offer and send bid for the most profitable offer

                auction_time = respond["timeout"]
                time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time

                ### Calculate a bid for an offer (more than one?)
                ### Should implement start_time/ timeout for fetching offers?

                offer_id = offers[1]['offer_id']
                if carrier.carrier_id == 'shachar':
                    bid = 90 
                elif carrier.carrier_id == 'lorenz':
                    bid = 100

                elif carrier.carrier_id == 'max':
                    offer_id = offers[0]['offer_id']
                    bid = 80

                respond = carrier.send_bid(offer_id, bid)  # Send a bid
                print("\n Auctioneer response to bid:")
                print(json.dumps(respond, indent=2, default=str))
                message =  "Auctioneer response to bid: " + json.dumps(respond, indent=2, default=str)
                socketio.emit(carrierId, {'message': message })

                auction_time = respond["timeout"]
                time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time

                respond = carrier.request_auction_results()  # Request auction results
                print("\n Auctioneer response to request_results:")
                print(json.dumps(respond, indent=2, default=str))
                message =  "Auctioneer response to request_results: " + json.dumps(respond, indent=2, default=str)
                socketio.emit(carrierId, {'message': message })

                if not respond["payload"]["next_round"]:
                    print("\nAuction day over")
                    socketio.emit(carrierId, {'message': "Auction day over" })
                    exit()

                auction_time = respond["timeout"]

                ### Save the relevant results (offer sold/ winning bid)
                time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time



            
