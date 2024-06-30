import yaml
import utilities as utils
import random

class CostModel:

    def __init__(self, cost_model):
        self.a1 = cost_model['base_price']
        self.a2 = cost_model['loadingRate']
        self.b1 = cost_model['kilometerPrice']
        self.b2 = cost_model['kilometerCost']
        self.sell_threshhold = cost_model['sell_threshold']
        self.buy_threshhold = cost_model['buy_threshold']
        print(self.sell_threshhold)

    def get_mariginal_revenue(self, loc_pickup, loc_dropoff):
        margin_revenue = self.a1 + self.a2*utils.get_distance(loc_pickup, loc_dropoff)
        return margin_revenue
    
    def get_total_revenue(self):
        pass


    def get_marginal_cost(self, marginal_distance):
        margin_cost = self.b1 + self.b2*marginal_distance
        return margin_cost

    def get_total_cost(self):
        pass

    def get_marginal_profit(self):
        pass

    def get_total_profit(self):
        pass        