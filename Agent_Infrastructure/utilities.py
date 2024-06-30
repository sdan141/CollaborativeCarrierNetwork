import numpy as np
import pandas as pd
#import matplotlib
#from matplotlib import pyplot 
from tabulate import tabulate

def load_transport_requests(file_path, n): 
    try:
        deliveries_df = pd.read_csv(file_path) # eventually clean data first
    except FileNotFoundError:
        deliveries_df = generate_random_locations(n)
    print(f"\nAll deliveries: \n")
    print(tabulate(deliveries_df, headers='keys', tablefmt='psql'))
    return deliveries_df 

def generate_random_locations(n=7): 
    #deliveries = np.random.uniform((-100,-100,-100,-100),(100,100,100,100),(10,4))
    # New York City harbor coordinates reach
    deliveries = np.round(np.random.uniform((81.9698,37.5281,81.9698,37.5281),(93.2898,46.2281,93.2898,46.2281),(n,4)), 3)
    deliveries_df = pd.DataFrame(deliveries,columns=['pickup_long','pickup_lat','delivery_long','delivery_lat'])
    print(f"\nAll deliveries: \n")
    print(tabulate(deliveries_df, headers='keys', tablefmt='psql'))
    return deliveries_df 

def generate_random_requests(harbor='NYC', n=10): 
    if harbor == 'NYC':
        # New York City harbor coordinates reach
        deliveries = np.round(np.random.uniform((81.9698,37.5281,81.9698,37.5281,100,5000),(93.2898,46.2281,93.2898,46.2281,4000,10000),(n,6)), 2)
    else:
        deliveries = np.random.uniform((0,0,0,0,20,300),(1000,1000,1000,1000,200,1000),(n,6))
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

def get_distance(p0, p1, mode="euclid"):
    p_0 = (p0["pos_x"], p0["pos_y"])
    p_1 = (p1["pos_x"], p1["pos_y"])
    if mode=="euclid":
        distance = np.linalg.norm(np.array(p_0) - np.array(p_1))
    elif mode=="manhattan":
        distance = np.sum(np.abs(np.array(p_0) - np.array(p_1)))
    return distance
    

def random_cost_model():
    costs = np.round(np.random.uniform((700,185,50,23),(750,215,55,28),4),2)
    print(f"\nCarrier random cost model:\n a_1 = {round(costs[0],2)}, a_2 = {round(costs[1],2)}, \
                                           b_1 = {round(costs[2],2)}, b_2 = {round(costs[3],2)}\n")
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

def get_key_from_bundle_by_first_element(dictionary, value):
    for key, val in dictionary.items():
        if val[0] == value:
            return key
    return None

def print_offer_list(offer_dictionaries):
    offers = [flatten_and_round_dict(offer) for offer in offer_dictionaries]
    offers_df = pd.DataFrame(offers).drop(columns=['offer_id'])
    print(tabulate(offers_df, headers='keys', tablefmt='psql'))

def save_results_to_csv(date, old_profit, new_profit, difference, increase):
    try:
        df = pd.read_csv('ccn_stats.csv')
    except FileNotFoundError:
        df = pd.DataFrame(columns=['date', 'old_profit', 'new_profit', 'difference', 'increase'])

    new_data = {'date': date,
              'old_profit': old_profit,
              'new_profit': new_profit,
              'difference': difference,
              'increase': increase}
    
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv('ccn_stats.csv', index=False)