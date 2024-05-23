from flask import Flask, render_template, request, jsonify
from generate_requests import create_random_locations, assign_deliveries, assign_revenues
from draw_graph import show_tour
import io
import base64
from auctioneer_class import *
from carrier_class import *
from carrier_start import start_carrier
from calculate_tour import get_optimal_tour, create_tour_data

from flask_socketio import SocketIO, emit
import pandas as pd

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('selection.html')

@app.route('/selection')
def selection():
    return render_template('selection.html')

@app.route('/carrier')
def carrier():
    return render_template('carrier.html')

@app.route('/auctioneer')
def auctioneer():
    return render_template('auctioneer.html')
    auctioneer = Auctioneer()
    auctioneer.start_server()

@app.route('/generate_deliveries', methods=['GET'])
def generate_deliveries():
    locations = create_random_locations()
    deliveries = assign_deliveries(locations)
    revenue_list = assign_revenues(deliveries)
    
    data = create_tour_data(locations, deliveries)
    tour_calculation = get_optimal_tour(data)

    revenue_total = round(sum(revenue_list), 2)
    distance = tour_calculation['distance']
    cost = round(distance * 0.05, 2)
    profit = round(revenue_total - cost, 2)

    fig = show_tour(locations, tour_calculation['optimalTour'])
    output = io.BytesIO()
    fig.savefig(output, format='png')
    output.seek(0)
    plot_base64 = base64.b64encode(output.getvalue()).decode('utf-8')

    response = {
        'plot': plot_base64,
        'locations': locations,
        'deliveries': deliveries,
        'revenueList': revenue_list,
        'revenueTotal': revenue_total,
        'cost': cost,
        'profit': profit,
        'distance': distance,
    }

    return jsonify(response)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}

@app.route('/upload_deliveries', methods=['POST'])
def upload_deliveries():
    if 'file' not in request.files:
        print("No file part") 
    
    file = request.files['file']
    
    if file.filename == '':
        print("No selected file") 
    
    if file and allowed_file(file.filename):
        try:
            df = pd.read_excel(file)
            result = process_data(df)
            return result
        except Exception as e:
            print(f"Error: {str(e)}") 
        
    print("File not allowed") 

def process_data(file):
    depot = []
    deliveries = []
    revenue_list = []
    depot.append(file.columns[1])
    depot.append(file.columns[2])
    depot = tuple(depot)
    print(f"Depot location: {depot}")
    locations = [depot]
    

    row_count = len(file)

    for row in range(1, row_count):
        pickup_x = file.iloc[row, 1]
        pickup_y = file.iloc[row, 2]
        dropoff_x = file.iloc[row, 3]
        dropoff_y = file.iloc[row, 4]
        revenue = file.iloc[row, 5]
        revenue_list.append(revenue)
        locations.append((pickup_x, pickup_y))
        locations.append((dropoff_x, dropoff_y))

    deliveries.append([1, 2])
    deliveries.append([3, 4])
    deliveries.append([5, 6])
    deliveries.append([7, 8])

    data = create_tour_data(locations, deliveries)
    tour_calculation = get_optimal_tour(data)

    revenue_total = round(sum(revenue_list), 2)
    distance = tour_calculation['distance']
    cost = round(distance * 0.05, 2)
    profit = round(revenue_total - cost, 2)

    fig = show_tour(locations, tour_calculation['optimalTour'])
    output = io.BytesIO()
    fig.savefig(output, format='png')
    output.seek(0)
    plot_base64 = base64.b64encode(output.getvalue()).decode('utf-8')

    response = {
        'plot': plot_base64,
        'locations': locations,
        'deliveries': deliveries,
        'revenueList': revenue_list,
        'revenueTotal': revenue_total,
        'cost': cost,
        'profit': profit,
        'distance': distance,
    }

    return jsonify(response)

@app.route('/init_auctioneer')
def init_auctioneer():
    auctioneer = Auctioneer(socketio)
    auctioneer.start_server()

@app.route('/init_carrier', methods=['POST'])
def init_carrier():
    company_name = request.json.get('companyName')
    locations = request.json.get('locations')
    deliveries = request.json.get('deliveries')
    revenueList = request.json.get('revenueList')
    start_carrier(company_name, locations, deliveries, revenueList, socketio)

if __name__ == '__main__':
    socketio.run(app, debug=True)



