from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, join_room, leave_room
import io
import base64
import sys
import os
import uuid

from generate_requests import create_random_locations, assign_deliveries
from draw_graph import show_tour
from calculate_tour import get_optimal_tour, create_tour_data
from handle_files import handle_file
from cost_model_old import get_cost_list, get_revenue_list, get_profit_list

from auctioneer_server import AuctioneerServer
from carrier import Carrier

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

@app.route('/generate_deliveries', methods=['GET'])
def generate_deliveries():
    locations = create_random_locations()
    deliveries = assign_deliveries(locations)
    response = create_response(locations, deliveries)
    return response

@app.route('/upload_deliveries', methods=['POST'])
def upload_deliveries():
    data = handle_file(request.files)
    response = create_response(data['locations'], data['deliveries'])
    return response

BASE_PRICE = 20
LOADING_RATE = 10
KILOMETER_PRICE = 2
KILOMETER_COST = 1

def create_response(locations, deliveries):
    data = create_tour_data(locations, deliveries)
    tour_calculation = get_optimal_tour(data)
    
    # Matplot graph as png
    fig = show_tour(locations, tour_calculation['optimalTour'])
    output = io.BytesIO()
    fig.savefig(output, format='png')
    output.seek(0)
    plot_base64 = base64.b64encode(output.getvalue()).decode('utf-8')

    # Money calculations
    distance_total = tour_calculation['distance']
    individual_revenues = get_revenue_list(locations, deliveries, BASE_PRICE, KILOMETER_PRICE) 
    individual_real_costs = get_cost_list(locations, deliveries, distance_total, LOADING_RATE, KILOMETER_COST)
    individual_profits = get_profit_list(individual_revenues, individual_real_costs)
    revenue_total = round(sum(individual_revenues), 2)
    cost_total = round(len(deliveries) * LOADING_RATE + (distance_total / 1000) * KILOMETER_COST, 2)
    profit_total = round(revenue_total - cost_total, 2)

    print(f"Revenues: {individual_revenues}")
    print(f"Costs: {individual_real_costs}")
    print(f"Profits: {individual_profits}")

    response = {
        'plot': plot_base64,
        'locations': locations,
        'deliveries': deliveries,
        'revenueList': individual_revenues,
        'costList': individual_real_costs,
        'profitList': individual_profits,
        'revenueTotal': revenue_total,
        'cost': cost_total,
        'profit': profit_total,
        'distance': distance_total,
    }

    return jsonify(response)

@app.route('/init_auctioneer')
def init_auctioneer():
    auctioneer_server = AuctioneerServer(socketio)
    auctioneer_server.start_server()

@app.route('/init_carrier', methods=['POST'])
def init_carrier():
    company_name = request.json.get('companyName')
    # locations = request.json.get('locations')
    # profit_list = request.json.get('profitList')
    carrier = Carrier(company_name, socketio, config_file=None, deliveries_file=None)
    carrier.start()
"""
@socketio.on('connect')
def handle_connect():
    user_id = 'test_id' # str(uuid.uuid4())
    session['user_id'] = user_id
    join_room(user_id)
    print(f"User: {user_id}")

@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get('user_id')
    if user_id:
        leave_room(user_id)
"""

@socketio.on('start_expensive_task')
def handle_start_expensive_task(data):
    user_id = session.get('user_id')
    if user_id:
        # Start the task asynchronously to avoid blocking
        socketio.start_background_task(expensive_task, data, user_id)

def expensive_task(data, user_id):
    # Simulate a long-running task
    import time
    time.sleep(10)  # Replace this with actual processing logic
    result = {'status': 'Task completed', 'data': data}
    socketio.emit('task_completed', result, room=user_id)

if __name__ == '__main__':
    socketio.run(app, port=int(sys.argv[1]), debug=True)
