from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


import yaml
import os

script_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
config_path = os.path.join(parent_dir, 'config', 'carrier_config.yaml')

# Load the configuration file
with open(config_path, 'r') as config_file:
    config = yaml.safe_load(config_file)

vehicle_maximum_distance = config['constants']['vehicle_maximum_distance']
num_vehicles = config['constants']['num_vehicles']
depot_location = config['constants']['num_vehicles']

# VEHICLE_MAXIMUM_DISTANCE = 5000
# NUM_VEHICLES = 1
# DEPOT_LOCATION = 0

class AlgorithmBase():
    
    def __init__(self, locations, assignments):
        self.locations = locations
        self.assignments = assignments

    def filter_requests_by_index(self, ignore):
        # Remove the unwanted indices from locations and create a mapping
        index_mapping = {}
        new_index = 0

        locations = []
        for i in ignore:
            for old_index, loc in enumerate(self.locations):
                if loc not in [self.locations[j] for j in self.assignments[i]]:
                    # the location is not the pickup or dropoff location
                    # of the assignment (transport request) we wish to ignore
                    locations.append(loc)
                    index_mapping[old_index] = new_index
                    new_index += 1

        # Update the assignment list with the new indices, omitting assignments that should be ignored
        assignments = [[index_mapping[p], index_mapping[d]] for p, d in self.assignments if p in index_mapping and d in index_mapping]
        return locations, assignments

    def create_distance_matrix(self, locations):
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

    def create_tour_data(self, ignore_indices = [], include_pickups=[], include_dropoffs=[]): 
        '''Create data required for 'get_optimal_tour()'.

        Args:
            locations (list of tuples): List of tuples containing (x, y) coordinates.
            assigned_deliveries (list of lists): List of pairs [x, y] representing assigned delivery locations.

        Returns:
            dict: Dictionary containing tour data.
        '''
        if ignore_indices:
            locations, assignmets = self.filter_requests_by_index(ignore_indices)
        else: 
            locations, assignmets = self.locations, self.assignments
        
        if include_pickups:
            for include_location in zip(include_pickups, include_dropoffs): # zip( [(1,2),()], [(3,4),()] ) -> [ ( (1,2), (3,4) ), () ]
                locations.extend(list(include_location)) 
                assignmets.append([len(locations)-2, len(locations)-1])
                
        #print(f"\nAfter create_tour_data locations: {[(round(ll,3),round(lr,3)) for ll, lr in locations]} \nand assignments: {assignmets}\n")
        data = {}
        data["distance_matrix"] = self.create_distance_matrix(locations)
        data["pickups_deliveries"] = assignmets
        data["num_vehicles"] = num_vehicles
        data["depot"] = depot_location
        return data

    def calculate_optimal_tour(self, data):
        '''Calculates the optimal tour.

        Args:
            data (dict): Dictionary containing necessary data for routing.

        Returns:
            list: List representing the optimal tour (assignments) and distance as float
        '''
        manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), data["num_vehicles"], data["depot"])
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            """Returns the manhattan distance between the two nodes."""
            # Convert from routing variable Index to distance matrix NodeIndex.
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(data["distance_matrix"][from_node][to_node])

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add Distance constraint.
        dimension_name = "Distance"
        routing.AddDimension(
            transit_callback_index,
            0,  # no slack
            vehicle_maximum_distance,
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

    # The main function that calles create_tour_data and calculate_optimal_tour
    def get_optimal_tour(self, ignore_indices=[], include_pickups=[], include_dropoffs=[]): 
        data = self.create_tour_data(ignore_indices, include_pickups, include_dropoffs)
        return self.calculate_optimal_tour(data)