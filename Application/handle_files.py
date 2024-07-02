import pandas as pd
import utilities as utils
from tour_calculation import create_tour_data, get_optimal_tour
from create_plot import create_plot
# from utilities import get_cost_list, get_revenue_list, get_optimal_tour, get_profit_list, create_plot

def handle_file(uploaded_file):
    if 'file' not in uploaded_file:
        print("No file part") 
    
    file = uploaded_file['file']
    
    if file.filename == '':
        print("No selected file") 
    
    if file and allowed_file(file.filename):
        try:
            df = pd.read_excel(file)
            data = process_excel(df)
            return data
        except Exception as e:
            print(f"Error: {str(e)}") 
    
    print("File not allowed")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}

def process_excel(file):
    locations = []
    assignments = []
    
    # Add depot
    depot = []
    depot.append(file.columns[1])
    depot.append(file.columns[2])
    depot = tuple(depot)
    locations.append(depot)

    # Get settings
    base_price = file.iloc[0, 1]
    kilometer_price = file.iloc[1, 1]
    loading_rate = file.iloc[2, 1]
    kilometer_cost = file.iloc[3, 1]
    sell_threshhold = file.iloc[4, 1]
    buy_threshhold = file.iloc[5, 1]

    # Add transport requests
    for row in range(7, len(file)):
        pickup_x = file.iloc[row, 1]
        pickup_y = file.iloc[row, 2]
        dropoff_x = file.iloc[row, 3]
        dropoff_y = file.iloc[row, 4]
        locations.append((pickup_x, pickup_y))
        locations.append((dropoff_x, dropoff_y))

    # Map deliveries
    multiplier = 0
    delivery_amount = int((len(locations) - 1 ) / 2)
    for i in range(0, delivery_amount):
        assignments.append([i + (1 + multiplier), i + (2 + multiplier)])
        multiplier = multiplier + 1

    # Calculate the data
    tour_data = create_tour_data(locations, assignments)
    tour_calculation = get_optimal_tour(tour_data) 
    
    distance_total = tour_calculation['distance']
    individual_revenues = get_revenue_list(locations, assignments, base_price, kilometer_price) 
    individual_real_costs = get_cost_list(locations, assignments, loading_rate, kilometer_cost)
    individual_profits = get_profit_list(individual_revenues, individual_real_costs)
    revenue_total = round(sum(individual_revenues), 2)
    cost_total = round(len(assignments) * loading_rate + (distance_total / 1000) * kilometer_cost, 2)
    profit_total = round(revenue_total - cost_total, 2)
    plot = create_plot(locations, tour_calculation["optimalTour"], "#D26466")


    data = {
        "plot": plot,
        'locations': locations,
        'deliveries': assignments,
        "profitList": individual_profits,
        "revenueList": individual_revenues,
        "costList": individual_real_costs,
        "revenueTotal": revenue_total,
        "cost": cost_total,
        "profit": profit_total,
        "distance": distance_total,
        "basePrice": base_price,
        "loadingRate": loading_rate,
        "kilometerPrice": kilometer_price,
        "kilometerCost": kilometer_cost,
        "sell_threshold": sell_threshhold,
        "buy_threshold": buy_threshhold
    }

    return data

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
