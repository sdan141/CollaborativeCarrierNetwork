from carrier_class import *
import sys
import utilities as utils

def start_carrier(carrier_name, locations, revenu_list, socketio):
    carrier = Carrier(carrier_name, socketio) # Add more data?
    auct_response = carrier.register()
    print("\n Auctioneer response to register:")
    print(json.dumps(auct_response, indent=2, default=str))
    
    if auct_response['payload']['status'] == 'OK':
        carrier.socketio.emit(carrier.carrier_id, {'message': "Registered successfully!"})
        select_transport_requests(carrier, locations, revenu_list)


def select_transport_requests(carrier, locations, revenu_list):
        """ Decide which offers to send (i.e. calculate offers below threshold)
        
            # Example offer
            pickup = {"pos_x": "10", "pos_y": "-10"}
            dropoff = {"pos_x": "0", "pos_y": "0"}
        """
        carrier.socketio.emit(carrier.carrier_id, {'message': "Selecting transport requests..."})
        requests_below_thresh_list = []
        
        if(carrier.carrier_id == 'Lorenz' or carrier.carrier_id == 'Shachar' or carrier.carrier_id == 'Max'):
            file_path = f"example_TR_{carrier.carrier_id}.csv"
            deliveries_df = utils.read_transport_requests(file_path, carrier)
            requests_below_thresh_list = utils.get_requests_below_thresh(deliveries_df, carrier)
        else:
            requests_below_thresh_list = utils.get_requests_below_thresh_new(locations, revenu_list)
        
        for i in range(0, len(requests_below_thresh_list)):
            carrier.socketio.emit(carrier.carrier_id, {'message': f"Selected: {requests_below_thresh_list[i]}"})

        if requests_below_thresh_list:
            send_transport_requests(carrier, requests_below_thresh_list)
        else:
            carrier.socketio.emit(carrier.carrier_id, {'message': f"No requests below threshhold."}) 

def send_transport_requests(carrier, requests_below_thresh_list):
    carrier.socketio.emit(carrier.carrier_id, {'message': "Sending transport requests..."})
    for loc_pickup, loc_dropoff, profit in requests_below_thresh_list:
        auct_response = carrier.send_offer(loc_pickup, loc_dropoff, profit) # Send an offer
        print("\n Auctioneer response to offer:")
        print(json.dumps(auct_response, indent=2, default=str))
        message =  "Auctioneer response to offer: " + json.dumps(auct_response, indent=2, default=str)
        carrier.socketio.emit(carrier.carrier_id, {'message': message})
        ### Update transport network
    
    carrier.socketio.emit(carrier.carrier_id, {'message': "Waiting for other carriers..."})
    auction_time = auct_response["timeout"] # If auct_response["timeout"]!="NONE" else time.time()+30
    time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time
    request_offers(carrier)

def request_offers(carrier):
    carrier.socketio.emit(carrier.carrier_id, {'message': "Requesting offers..."})
    while True:
        auct_response = carrier.request_offers() # Request current offers
        
        print("\n Auctioneer response to request_offers:")
        print(json.dumps(auct_response, indent=2, default=str))
        message =  "Auctioneer response to request_offers: " + json.dumps(auct_response, indent=2, default=str)
        carrier.socketio.emit(carrier.carrier_id, {'message': message})
        
        offers = auct_response["payload"]["offer_list"]
        calculate_bids(carrier, offers)

        carrier.socketio.emit(carrier.carrier_id, {'message': "Waiting for auction start..."})
        auction_time = auct_response["timeout"]
        time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time

        ### Calculate a bid for an offer (more than one?)
        ### Should implement start_time/ timeout for fetching offers?

        bid = 60
        offer_id = offers[1]['offer_id']

        if carrier.carrier_id == 'shachar':
            bid = 90 
        elif carrier.carrier_id == 'lorenz':
            bid = 100
        elif carrier.carrier_id == 'max':
            bid = 80

        auct_response = carrier.send_bid(offer_id, bid)  # Send a bid
        print("\n Auctioneer response to bid:")
        print(json.dumps(auct_response, indent=2, default=str))
        message =  "Auctioneer response to bid: " + json.dumps(auct_response, indent=2, default=str)
        carrier.socketio.emit(carrier.carrier_Id, {'message': message })

        auction_time = auct_response["timeout"]
        time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time

        auct_response = carrier.request_auction_results()  # Request auction results
        print("\n Auctioneer response to request_results:")
        print(json.dumps(auct_response, indent=2, default=str))
        message =  "Auctioneer response to request_results: " + json.dumps(auct_response, indent=2, default=str)
        carrier.socketio.emit(carrier.carrier_Id, {'message': message })

        if not auct_response["payload"]["next_round"]:
            print("\nAuction day over")
            carrier.socketio.emit(carrier.carrier_Id, {'message': "Auction day over" })
            exit()

        auction_time = auct_response["timeout"]

        ### Save the relevant results (offer sold/ winning bid)
        time.sleep(abs(auction_time-time.time())+4)  # Wait to auction time

def calculate_bids(carrier, offers):
    carrier.socketio.emit(carrier.carrier_id, {'message': "Calculating bids..."})
    ## Calculate bids for each offer and send bid for the most profitable offer


            
