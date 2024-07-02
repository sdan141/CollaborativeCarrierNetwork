from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import sys
import os
import pandas as pd
import numpy as np
from tabulate import tabulate #FIXME
from tour_calculation import get_optimal_tour, create_tour_data
from create_plot import create_plot
from handle_files import get_cost_list, get_revenue_list, get_profit_list

# from utilities import generate_requests
from auctioneer_server import AuctioneerServer
from carrier import Carrier
from handle_files import handle_file

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    """Load selection.html"""
    return render_template('selection.html')

@app.route('/selection')
def selection():
    """Load selection.html"""
    return render_template('selection.html')

@app.route('/carrier')
def carrier():
    """Load carrier.html"""
    return render_template('carrier.html')

@app.route('/auctioneer')
def auctioneer():
    """Load auctioneer.html"""
    return render_template('auctioneer.html')

@app.route('/simulation')
def simulation():
    """Load simulation.html"""
    return render_template('simulation.html')

@app.route('/init_auctioneer')
def init_auctioneer():
    auctioneer_server = AuctioneerServer(socketio)
    auctioneer_server.start_server()

@app.route('/init_carrier', methods=['POST'])
def init_carrier():
    costs = request.json.get('costs')
    revenues = request.json.get('revenues')
    profits = request.json.get('profits')

    locations = request.json.get('locations')
    without_depot = locations[1:]
    list_pickup_x = []
    list_pickup_y = []
    list_dropoff_x = []
    list_dropoff_y = []

    for i in range(0, len(without_depot), 2):
        pickup_x, pickup_y = without_depot[i]
        dropoff_x, dropoff_y = without_depot[i + 1]
        list_pickup_x.append(pickup_x)
        list_pickup_y.append(pickup_y)
        list_dropoff_x.append(dropoff_x)
        list_dropoff_y.append(dropoff_y)

        
    data = {
        'pickup_long': list_pickup_x,
        'pickup_lat': list_pickup_y,
        'delivery_long': list_dropoff_x,
        'delivery_lat': list_dropoff_y,
        'revenue': revenues,
        'cost': costs,
        'profit': profits
    }
    
    dt_data = pd.DataFrame(data)
    print("\nUploaded deliveries:")
    print(tabulate(dt_data, headers='keys', tablefmt='psql'))
    company_name = request.json.get('companyName')
    
    price_model = {
        "base_price": request.json.get('basePrice'),
        "loadingRate": request.json.get('loadingRate'),
        "kilometerPrice": request.json.get('kilometerPrice'),
        "kilometerCost": request.json.get('kilometerCost'),
        "sell_threshold": request.json.get('sell_threshold'),
        "buy_threshold": request.json.get('buy_threshold')
    }
    
    carrier = Carrier(company_name, socketio, dt_data, locations[0], price_model)
    carrier.start()

@app.route('/generate_deliveries', methods=['POST'])
def generate_deliveries():
    # Get settings
    base_price = request.json.get('basePrice')
    kilometer_price = request.json.get('kilometerPrice')
    loading_rate = request.json.get('loadingRate')
    kilometer_cost = request.json.get('kilometerCost')
    sell_threshold = request.json.get('sell_threshold')
    buy_threshold = request.json.get('buy_threshold')

    locations = []
    assignments = []
    
    # Add depot
    depot = []
    depot.append(np.random.randint(-100, 100))
    depot.append(np.random.randint(-100, 100))
    depot = tuple(depot)
    locations.append(depot)

    # Add transport requests
    for i in range(0, 5):
        pickup_x = np.random.randint(-100, 100)
        pickup_y = np.random.randint(-100, 100)
        dropoff_x = np.random.randint(-100, 100)
        dropoff_y = np.random.randint(-100, 100)
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
    individual_revenues = get_revenue_list(locations, assignments, float(base_price), float(kilometer_price)) 
    individual_real_costs = get_cost_list(locations, assignments, float(loading_rate), float(kilometer_cost))
    individual_profits = get_profit_list(individual_revenues, individual_real_costs)
    revenue_total = round(sum(individual_revenues), 2)
    cost_total = round(len(assignments) * float(loading_rate) + (distance_total / 1000) * float(kilometer_cost), 2)
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
        "basePrice": float(base_price),
        "loadingRate": float(loading_rate),
        "kilometerPrice": float(kilometer_price),
        "kilometerCost": float(kilometer_cost),
        "sell_threshold": float(sell_threshold),
        "buy_threshold": float(buy_threshold)
    }

    return jsonify(data)

@app.route('/upload_deliveries', methods=['POST'])
def upload_deliveries():
    data = handle_file(request.files)
    return jsonify(data)

@app.route('/get_plot', methods=['POST'])
def get_plot():
    locations = request.json.get('locations')
    coordinates_tuples = list(map(tuple, locations))
    print(coordinates_tuples)

    # Map deliveries
    assignments = []
    multiplier = 0
    delivery_amount = int((len(locations) - 1 ) / 2)
    for i in range(0, delivery_amount):
        assignments.append([i + (1 + multiplier), i + (2 + multiplier)])
        multiplier = multiplier + 1
    
    tour_data = create_tour_data(coordinates_tuples, assignments)
    tour_calculation = get_optimal_tour(tour_data) 
    plot = create_plot(coordinates_tuples, tour_calculation["optimalTour"], "#3F704D")

    loading_rate = request.json.get('loadingRate')
    kilometer_cost = request.json.get('kilometerCost')
    total_cost = delivery_amount * float(loading_rate) + (float(tour_calculation["distance"]) / 1000) * float(kilometer_cost)

    data = {
        "plot": plot,
        "distance": tour_calculation["distance"],
        "cost": total_cost
    }

    return jsonify(data)

if __name__ == '__main__':
    socketio.run(app, port=int(sys.argv[1]), debug=True)
