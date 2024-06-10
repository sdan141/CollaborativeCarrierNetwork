from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import utilities as util

VEHICLE_MAXIMUM_DISTANCE = 3000
NUM_VEHICLES = 1
DEPOT_LOCATION = 0

class Routing():

    def __init__(self, deliveries_file):

        if not deliveries_file:
            self.deliveries_df = util.generate_random_requests()
            #self.pickupse = pickups
            #self.dropoffs = dropoffs




    def assign_deliveries(self, locations):
        pass

    def create_distance_matrix(self, locations):
        pass
