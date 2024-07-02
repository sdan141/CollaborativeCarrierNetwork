import utilities as utils
import random

class CostModel:

    def __init__(self, config_data):

        if not config_data:
            cost_model = utils.random_cost_model()
            self.threshold = random.randrange(325,330)
        else: 
            cost_model = config_data['cost_model']
            self.threshold = config_data['threshold']


        self.a1 = cost_model['a1']
        self.a2 = cost_model['a2']
        self.b1 = cost_model['b1']
        self.b2 = cost_model['b2']

    def get_mariginal_revenue(self, loc_pickup, loc_dropoff):
        margin_revenue = self.a1 + self.a2*utils.get_distance(loc_pickup, loc_dropoff, mode='manhattan')
        return margin_revenue

    def get_marginal_cost(self, marginal_distance, n_jobs=1):
        margin_cost = n_jobs * self.b1 + self.b2*marginal_distance
        return margin_cost

    def get_marginal_profit(self, marginal_revenue, marginal_cost):
        return marginal_revenue - marginal_cost
