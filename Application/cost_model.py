#import yaml
import utilities as util

class CostModel:

    def __init__(self, config_file):

        if not config_file:
            cost_model = util.random_cost_model()
        else: 
            with open(config_file, 'rb') as stream:
                try:
                   data_loaded = yaml.safe_load(stream)
                   cost_model = data_loaded['cost_model']
                except yaml.YAMLError as e:
                    print(e)

        self.a1 = cost_model['a1']
        self.a2 = cost_model['a2']
        self.b1 = cost_model['b1']
        self.b2 = cost_model['b2']
                
    def get_marginal_cost(offers, distance):
        pass

    def get_direct_cost(distance):
        pass

        