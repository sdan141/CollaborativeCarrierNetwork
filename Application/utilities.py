import numpy as np
import pandas as pd
#import matplotlib
#from matplotlib import pyplot 
from tabulate import tabulate

THRESHOLD = 9.2

def get_requests_below_thresh(locations, profit_list, thresh=THRESHOLD):
    """returns a list of """
    requests_list = []
    multiplier = 0
    for i in range(0, len(profit_list)):
        if(profit_list[i] < thresh):
            loc_pickup = {
                "pos_x": locations[i + (1 + multiplier)][0], 
                "pos_y": locations[i + (1 + multiplier)][1]
                }
            loc_dropoff = {
                "pos_x": locations[i + (2 + multiplier)][0], 
                "pos_y": locations[i + (2 + multiplier)][1]
                }
            profit = profit_list[i]
            requests_list.append((loc_pickup, loc_dropoff, profit))
        multiplier = multiplier + 1

    print(f"\n\nTransport request to send: \n{requests_list}\n")
    return requests_list



# Code below isnt used anymore except for the example_TR_Name.csv files

def read_transport_requests(file_path, carrier): # path?
    deliveries_df = pd.read_csv(file_path) # eventually clean data first
    print(f"\nAll deliveries: \n")
    carrier.socketio.emit(carrier.carrier_id, {'message': "All deliveries: "})
    print(tabulate(deliveries_df, headers='keys', tablefmt='psql'))
    carrier.socketio.emit(carrier.carrier_id, {'message': tabulate(deliveries_df, headers='keys', tablefmt='psql')})
    return deliveries_df 

def get_requests_below_thresh_old(df, carrier, thresh=100):
    """returns a list of """
    below_threshold = df[(df.profit).astype(float)<thresh]
    print(f"\n\nDeliveries below threshhold: \n")
    print(tabulate(below_threshold, headers='keys', tablefmt='psql'))
    carrier.socketio.emit(carrier.carrier_id, {'message': tabulate(below_threshold, headers='keys', tablefmt='psql')})

    requests_list = []
    if len(below_threshold) > 0:
        for i, transport_request in below_threshold.iterrows():
            delivery_point = transport_request.to_dict()
            delivery_point
            loc_pickup = {
                "pos_x": transport_request.pickup_long, 
                "pos_y": transport_request.pickup_lat
                }
            loc_dropoff = {
                "pos_x": transport_request.delivery_long, 
                "pos_y": transport_request.delivery_lat
                }
            profit = transport_request.profit
            requests_list.append((loc_pickup, loc_dropoff, profit))

    print(f"\n\nTransport request to send: \n{requests_list}\n")
    carrier.socketio.emit(carrier.carrier_id, {'message': f"Transport request to send: {requests_list}"})
    return requests_list


def evaluate_transport_request(transport_request):
    pass