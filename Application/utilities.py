import numpy as np
import pandas as pd
#import matplotlib
#from matplotlib import pyplot 
from tabulate import tabulate

from create_plot import create_plot

BASE_PRICE = 20
LOADING_RATE = 10
KILOMETER_PRICE = 2
KILOMETER_COST = 1

REQUEST_AMOUNT = 5
import random
from tour_calculation import create_tour_data, get_optimal_tour

def generate_requests(base_price, kilometer_price, loading_rate, kilometer_cost):
    locations, assignments = generate_random_locations()
    data = create_tour_data(locations, assignments)
    tour_calculation = get_optimal_tour(data)
    distance_total = tour_calculation['distance']
    individual_revenues = get_revenue_list(locations, assignments, base_price, kilometer_price) 
    individual_real_costs = get_cost_list(locations, assignments, loading_rate, kilometer_cost)
    individual_profits = get_profit_list(individual_revenues, individual_real_costs)
    revenue_total = round(sum(individual_revenues), 2)
    cost_total = round(len(assignments) * loading_rate + (distance_total / 1000) * kilometer_cost, 2)
    profit_total = round(revenue_total - cost_total, 2)
    plot = create_plot(locations, tour_calculation["optimalTour"])

    response = {
        'plot': plot,
        'locations': locations,
        'deliveries': assignments,
        'revenueList': individual_revenues,
        'costList': individual_real_costs,
        'profitList': individual_profits,
        'revenueTotal': revenue_total,
        'cost': cost_total,
        'profit': profit_total,
        'distance': distance_total,
    }

    return response

def generate_random_locations(): 
    depot= (round(random.uniform(-100, 100), 2), round(random.uniform(-100, 100), 2))
    locations = [depot]
    assignments = []
    multiplier = 0
    data = []
    for i in range(0, REQUEST_AMOUNT):
        pickup_x= round(random.uniform(-100, 100), 2)
        pickup_y = round(random.uniform(-100, 100), 2)
        pickup = (pickup_x, pickup_y)
        locations.append(pickup) 

        dropoff_x= round(random.uniform(-100, 100), 2)
        dropoff_y = round(random.uniform(-100, 100), 2)
        dropoff = (dropoff_x, dropoff_y)
        locations.append(dropoff) 
        assignments.append([i + 1 + multiplier , i + 2 + multiplier])
        data.append([pickup_x, pickup_y, dropoff_x, dropoff_y])
    dt_deliveries = pd.DataFrame(data, columns=['pickup_long', 'pickup_lat', 'delivery_long','delivery_lat'])
    return locations, assignments

def get_revenue_list(locations, deliveries, base_price, kilometer_price):
    # Preis für request = Basisrate + Kilometerpreis * Distanz zwischen punkten
    revenues = []
    multiplier = 0
    for i in range(0, len(deliveries)):
        first_node = locations[i + 1 + multiplier]
        second_node = locations[i + 2 + multiplier]
        node_distance = round(abs(first_node[0] - second_node[0]) + abs(first_node[1] - second_node[1]), 2)
        revenue = round(base_price + kilometer_price * (node_distance / 1000), 2)
        revenues.append(revenue) 
        multiplier = multiplier + 1
    return revenues

def get_cost_list(locations, deliveries, loading_cost, kilometer_cost):
    # Cost für request = Laderate + Kilometerkosten * Auftrags distanz
    costs = []
    multiplier = 0
    original_data = create_tour_data(locations, deliveries)
    original_tour = get_optimal_tour(original_data)
    original_distance = original_tour['distance']
    for i in range(0, len(deliveries)):
        locations_without_request = locations[:]
        del locations_without_request[i + 1 + multiplier]
        del locations_without_request[i + 1 + multiplier]
        
        deliveries_without_request = deliveries[:]
        del deliveries_without_request[-1]

        data = create_tour_data(locations_without_request, deliveries_without_request)
        tour_calculation_without_request = get_optimal_tour(data)
        distance_without_request = tour_calculation_without_request['distance']
        
        request_distance = original_distance - distance_without_request
        cost = round(loading_cost + kilometer_cost * (request_distance / 1000), 2)
        costs.append(cost) 
        multiplier = multiplier + 1
    return costs

def get_profit_list(individual_revenues, individual_real_cost):
    profit_list = []

    for i in range(0, len(individual_revenues)):
        individual_profit = round(individual_revenues[i] - individual_real_cost[i], 2)
        profit_list.append(individual_profit)

    return profit_list






"""
def read_transport_requests(file_path): # path?
    deliveries_df = pd.read_csv(file_path) # eventually clean data first
    print(f"\nAll deliveries: \n")
    print(tabulate(deliveries_df, headers='keys', tablefmt='psql'))
    return deliveries_df 


def generate_random_locations(): 
    deliveries = np.random.uniform((-100,-100,-100,-100),(100,100,100,100),(5,4))
    deliveries_df = pd.DataFrame(deliveries,columns=['pickup_long','pickup_lat','delivery_long','delivery_lat'])
    deliveries_df = deliveries_df.round(2)
    print(f"\nAll deliveries: \n")
    print(tabulate(deliveries_df, headers='keys', tablefmt='psql'))
    return deliveries_df 


def generate_random_requests(): 
    deliveries = np.random.uniform((0,0,0,0,20,300),(1000,1000,1000,1000,200,1000),(5,6))
    deliveries_df = pd.DataFrame(deliveries,columns=['pickup_long','pickup_lat','delivery_long','delivery_lat','profit', 'revenue'])
    print(f"\nAll deliveries: \n")
    print(tabulate(deliveries_df, headers='keys', tablefmt='psql'))
    return deliveries_df 
"""
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
    costs = np.random.uniform((256,32,8,4),(512,64,16,8),4)
    print(f"\nCarrier random cost model:\n a_1 = {round(costs[0],2)}, a_2 = {round(costs[1],2)}, b_1 = {round(costs[2],2)}, b_2 = {round(costs[3],2)}\n")
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

