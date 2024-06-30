from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import sys
import os
import pandas as pd
from tabulate import tabulate #FIXME


from utilities import generate_requests
from auctioneer_server import AuctioneerServer
from carrier import Carrier
from handle_files import create_csv

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
    print(profits)

    locations = request.json.get('locations')
    without_depot = locations[1:]
    list_pickup_x = []
    list_pickup_y = []
    list_dropoff_x = []
    list_dropoff_y = []

    for i in range(0, len(without_depot), 2):
        pickup_x, pickup_y = locations[i]
        dropoff_x, dropoff_y = locations[i + 1]
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
    print("All deliveries:\n")
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
    base_price = request.json.get('basePrice')
    kilometer_price = request.json.get('kilometerPrice')
    loading_rate = request.json.get('loadingRate')
    kilometer_cost = request.json.get('kilometerCost')
    data = generate_requests(float(base_price), float(kilometer_price), float(loading_rate), float(kilometer_cost))
    return jsonify(data)

# @app.route('/upload_deliveries', methods=['POST'])
# def upload_deliveries():
    # data = handle_file(request.files)
    # response = create_response(data['locations'], data['deliveries'])
    # return response

if __name__ == '__main__':
    socketio.run(app, port=int(sys.argv[1]), debug=True)
