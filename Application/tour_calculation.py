from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

VEHICLE_MAXIMUM_DISTANCE = 3000
NUM_VEHICLES = 1
DEPOT_LOCATION = 0

def create_tour_data(locations, assigned_deliveries):
    '''Create data required for 'get_optimal_tour()'.

    Args:
        locations (list of tuples): List of tuples containing (x, y) coordinates.
        assigned_deliveries (list of lists): List of pairs [x, y] representing assigned delivery locations.

    Returns:
        dict: Dictionary containing tour data.
    '''
    data = {}
    data["distance_matrix"] = create_distance_matrix(locations)
    data["pickups_deliveries"] = assigned_deliveries
    data["num_vehicles"] = NUM_VEHICLES
    data["depot"] = DEPOT_LOCATION
    return data


def create_distance_matrix(locations):
    '''Create distance matrix using taxicab geometry. https://en.wikipedia.org/wiki/Taxicab_geometry
    
    Args:
        locations (list of tuples): List of locations (x, y).
    
    Returns:
        list of lists: Distance matrix. https://en.wikipedia.org/wiki/Distance_matrix 
    '''
    dist_mat = []
    for x in locations:
        distance_for_location_x = []
        for y in locations:
            distance = round(abs(x[0] - y[0]) + abs(x[1] - y[1]), 2)
            distance_for_location_x.append(distance) 
        dist_mat.append(distance_for_location_x) 
    return dist_mat 


def get_optimal_tour(data):
    '''Calculates the optimal tour.

    Args:
        data (dict): Dictionary containing necessary data for routing.

    Returns:
        list: List representing the optimal tour.
    '''
    manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), data["num_vehicles"], data["depot"])
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        """Returns the manhattan distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = "Distance"
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        VEHICLE_MAXIMUM_DISTANCE,
        True,  # start cumul to zero
        dimension_name,
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Define Transportation Requests.
    for request in data["pickups_deliveries"]:
        pickup_index = manager.NodeToIndex(request[0])
        delivery_index = manager.NodeToIndex(request[1])
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        routing.solver().Add(
            routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index)
        )
        routing.solver().Add(
            distance_dimension.CumulVar(pickup_index)
            <= distance_dimension.CumulVar(delivery_index)
        )

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    )

    solution = routing.SolveWithParameters(search_parameters)
    optimalTour = []
    vehicle_id = 0
    total_distance = 0
    index = routing.Start(vehicle_id)
    route_distance = 0
    while not routing.IsEnd(index):
        optimalTour.append(str(manager.IndexToNode(index)))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(
            previous_index, index, vehicle_id
        )
        total_distance += route_distance
    optimalTour.append(str(manager.IndexToNode(index)))

    result = {
        'optimalTour': optimalTour,
        'distance': total_distance,
    }

    return result