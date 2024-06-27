import yaml
import utilities as utils
import random

class CostModel:

    def __init__(self, config_file):

        if not config_file:
            cost_model = utils.random_cost_model()
            self.threshold = random.randrange(500,550)
        else: 
            with open(config_file, 'rb') as stream:
                try:
                   data_loaded = yaml.safe_load(stream)
                   cost_model = data_loaded['cost_model']
                   self.threshold = data_loaded['threshold']
                except yaml.YAMLError as e:
                    print(e)

        self.a1 = cost_model['a1']
        self.a2 = cost_model['a2']
        self.b1 = cost_model['b1']
        self.b2 = cost_model['b2']

    def get_mariginal_revenue(self, loc_pickup, loc_dropoff):
        margin_revenue = self.a1 + self.a2*utils.get_distance(loc_pickup, loc_dropoff, mode='manhattan')
        return margin_revenue
    
    def get_total_revenue(self):
        pass


    def get_marginal_cost(self, marginal_distance, n_jobs=1):
        margin_cost = n_jobs * self.b1 + self.b2*marginal_distance
        return margin_cost

    def get_total_cost(self):
        pass

    def get_marginal_profit(self):
        pass

    def get_total_profit(self):
        pass        