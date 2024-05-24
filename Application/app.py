from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import io
import base64

from generate_requests import create_random_locations, assign_deliveries, assign_revenues
from draw_graph import show_tour
from auctioneer_class import *
from carrier_class import *
from carrier_start import start_carrier
from calculate_tour import get_optimal_tour, create_tour_data
from handle_files import handle_file

app = Flask(__name__)
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

@app.route('/generate_deliveries', methods=['GET'])
def generate_deliveries():
    locations = create_random_locations()
    deliveries = assign_deliveries(locations)
    revenue_list = assign_revenues(deliveries)
    response = create_response(locations, deliveries, revenue_list)
    return response

@app.route('/upload_deliveries', methods=['POST'])
def upload_deliveries():
    data = handle_file(request.files)
    response = create_response(data['locations'], data['deliveries'], data['revenue_list'])
    return response

def create_response(locations, deliveries, revenue_list):
    data = create_tour_data(locations, deliveries)
    tour_calculation = get_optimal_tour(data)
    
    # Matplot graph as png
    fig = show_tour(locations, tour_calculation['optimalTour'])
    output = io.BytesIO()
    fig.savefig(output, format='png')
    output.seek(0)
    plot_base64 = base64.b64encode(output.getvalue()).decode('utf-8')

    # Cost calculations
    revenue_total = round(sum(revenue_list), 2)
    distance = tour_calculation['distance']
    cost = round(distance * 0.05, 2)
    profit = round(revenue_total - cost, 2)

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
    start_carrier(company_name, locations, revenueList, socketio)

if __name__ == '__main__':
    socketio.run(app, debug=True)



