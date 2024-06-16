import numpy as np
import pandas as pd
#import matplotlib
#from matplotlib import pyplot 
from tabulate import tabulate

def read_transport_requests(file_path): # path?
    deliveries_df = pd.read_csv(file_path) # eventually clean data first
    print(f"\nAll deliveries: \n")
    print(tabulate(deliveries_df, headers='keys', tablefmt='psql'))
    return deliveries_df 

def generate_random_locations(): 
    deliveries = np.random.uniform((0,0,0,0),(300,300,300,300),(5,4))
    deliveries_df = pd.DataFrame(deliveries,columns=['pickup_long','pickup_lat','delivery_long','delivery_lat'])
    print(f"\nAll deliveries: \n")
    print(tabulate(deliveries_df, headers='keys', tablefmt='psql'))
    return deliveries_df 

def generate_random_requests(): 
    deliveries = np.random.uniform((0,0,0,0,20,300),(1000,1000,1000,1000,200,1000),(5,6))
    deliveries_df = pd.DataFrame(deliveries,columns=['pickup_long','pickup_lat','delivery_long','delivery_lat','profit', 'revenue'])
    print(f"\nAll deliveries: \n")
    print(tabulate(deliveries_df, headers='keys', tablefmt='psql'))
    return deliveries_df 

def get_requests_below_thresh(df ,thresh=100):
    """returns a list of """
    below_threshold = df[(df.profit).astype(float)<thresh]
    print(f"\n\ndeliveries below threshhold: \n")
    print(tabulate(below_threshold, headers='keys', tablefmt='psql'))

    requests_list = []
    if len(below_threshold) > 0:
        for i, transport_request in below_threshold.iterrows():
            loc_pickup = {
                "pos_x": transport_request.pickup_long, 
                "pos_y": transport_request.pickup_lat
                }
            loc_dropoff = {
                "pos_x": transport_request.delivery_long, 
                "pos_y": transport_request.delivery_lat
                }
            profit = transport_request.profit
            revenue = transport_request.revenue
            requests_list.append((loc_pickup, loc_dropoff, profit, revenue))

    print(f"\n\nTransport request to send: \n{requests_list}\n")
    return requests_list

def get_distance(loc_pickup, loc_dropoff, mode="euclid"):
    pickup_point = (loc_pickup["pos_x"], loc_pickup["pos_y"])
    dropoff_point = (loc_dropoff["pos_x"], loc_dropoff["pos_y"])
    if mode=="euclid":
        distance = np.linalg.norm(np.array(pickup_point) - np.array(dropoff_point))
    elif mode=="manhattan":
        distance = np.sum(np.abs(np.array(pickup_point) - np.array(dropoff_point)))
    return distance
    

def random_cost_model():
    costs = np.random.uniform((100,25,10,5),(150,50,20,10),4)
    return {'a1': costs[0], 'a2': costs[1], 'b1': costs[2], 'b2': costs[3]}


def flatten_and_round_dict(d, decimal_places=4): # function for pretty printing
    flattened_dict = {}
    for key, value in d.items():
        if isinstance(value, dict): # if the value is a dictionary
            for sub_key, sub_value in value.items(): 
                if isinstance(sub_value, float):
                    if decimal_places:
                        sub_value = round(sub_value, decimal_places)
                flattened_dict[f"{key}_{sub_key}"] = sub_value
        else:
            flattened_dict[key] = value
    return flattened_dict

def dict_to_float(dict):
    for k, v in dict.items():
        dict[k] = float(v)
    return dict